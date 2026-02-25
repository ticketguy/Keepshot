"""Main FastAPI application"""
import re
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.core.logging import setup_logging, get_logger
from app.core import jwt as _jwt
from app.metrics import REQUEST_COUNT, REQUEST_LATENCY, ACTIVE_WEBSOCKETS
from app.services.scheduler import start_scheduler, stop_scheduler

# Setup logging
setup_logging(debug=settings.debug)
logger = get_logger(__name__)

# ── Path normaliser ────────────────────────────────────────────────────────────
# Replace UUIDs and numeric IDs in paths so Prometheus labels stay low-cardinality.
_UUID_RE = re.compile(
    r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)


def _normalise_path(path: str) -> str:
    return _UUID_RE.sub("/{id}", path)


# ── Metrics middleware ─────────────────────────────────────────────────────────

class MetricsMiddleware(BaseHTTPMiddleware):
    """Record per-route request counts and latencies for Prometheus."""

    async def dispatch(self, request, call_next):
        path = _normalise_path(request.url.path)
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        REQUEST_COUNT.labels(
            method=request.method,
            path=path,
            status_code=str(response.status_code),
        ).inc()
        REQUEST_LATENCY.labels(method=request.method, path=path).observe(duration)

        return response


# ── Rate limiting middleware ───────────────────────────────────────────────────
# Simple sliding-window counter, keyed on client IP.
# Exempt: /health, /metrics, /docs, /redoc, /openapi.json, /

_RATE_EXEMPT = frozenset(["/health", "/metrics", "/", "/docs", "/redoc", "/openapi.json"])


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls_per_minute: int, calls_per_hour: int):
        super().__init__(app)
        self.per_minute = calls_per_minute
        self.per_hour = calls_per_hour
        self._min_log: dict[str, list[float]] = defaultdict(list)
        self._hr_log: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request, call_next):
        if request.url.path in _RATE_EXEMPT:
            return await call_next(request)

        key = (request.client.host if request.client else "unknown")
        now = time.monotonic()

        # Prune and check minute window
        self._min_log[key] = [t for t in self._min_log[key] if now - t < 60]
        if len(self._min_log[key]) >= self.per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded — too many requests per minute"},
                headers={"Retry-After": "60"},
            )

        # Prune and check hour window
        self._hr_log[key] = [t for t in self._hr_log[key] if now - t < 3600]
        if len(self._hr_log[key]) >= self.per_hour:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded — too many requests per hour"},
                headers={"Retry-After": "3600"},
            )

        self._min_log[key].append(now)
        self._hr_log[key].append(now)
        return await call_next(request)


# ── WebSocket connection manager ───────────────────────────────────────────────

class ConnectionManager:
    """Manage WebSocket connections for real-time notifications"""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(user_id, []).append(websocket)
        logger.info("websocket_connected", user_id=user_id)

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info("websocket_disconnected", user_id=user_id)

    async def send_personal_message(self, user_id: str, message: dict):
        for connection in self.active_connections.get(user_id, []):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("websocket_send_failed", user_id=user_id, error=str(e))

    async def broadcast(self, message: dict):
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error("websocket_broadcast_failed", user_id=user_id, error=str(e))


manager = ConnectionManager()


# ── Application lifespan ───────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("keepshot_starting", version="1.0.0")
    start_scheduler()
    logger.info("scheduler_started")

    yield

    stop_scheduler()
    logger.info("scheduler_stopped")
    logger.info("keepshot_shutdown")


# ── App setup ──────────────────────────────────────────────────────────────────

app = FastAPI(
    title="KeepShot",
    description="AI-Powered Bookmark Monitoring System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(MetricsMiddleware)

app.add_middleware(
    RateLimitMiddleware,
    calls_per_minute=settings.rate_limit_per_minute,
    calls_per_hour=settings.rate_limit_per_hour,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health / metrics ───────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker and monitoring"""
    return JSONResponse(
        content={
            "status": "healthy",
            "version": "1.0.0",
            "service": "keepshot",
        }
    )


@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint"""
    ACTIVE_WEBSOCKETS.set(
        sum(len(conns) for conns in manager.active_connections.values())
    )
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ── WebSocket ──────────────────────────────────────────────────────────────────

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    token: Optional[str] = Query(None, description="JWT access token"),
):
    """
    WebSocket endpoint for receiving real-time notifications.

    **Authentication:** pass your JWT as a query parameter:
      ws://host/ws/{user_id}?token=<access_token>

    In DEBUG mode the token is optional (dev convenience).

    Message format (server → client):
    ```json
    {
      "type": "notification",
      "data": {
        "id": "...", "title": "...", "message": "...",
        "bookmark_id": "...", "created_at": "..."
      }
    }
    ```
    Ping/pong: send any text, receive `{"type": "pong", "data": <echo>}`.
    """
    # ── Authenticate ──────────────────────────────────────────────────────────
    if token:
        try:
            payload = _jwt.decode(token, settings.jwt_secret or "", algorithms=[settings.jwt_algorithm])
            token_user_id = payload.get("sub", "")
            if token_user_id != user_id:
                await websocket.close(code=4001, reason="Token user_id does not match path")
                return
        except _jwt.ExpiredSignatureError:
            await websocket.close(code=4001, reason="Token expired")
            return
        except _jwt.InvalidTokenError:
            await websocket.close(code=4001, reason="Invalid token")
            return
    elif not settings.debug:
        await websocket.close(code=4001, reason="Authentication required — provide ?token=<jwt>")
        return

    # ── Accept & serve ────────────────────────────────────────────────────────
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "pong", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception as e:
        logger.error("websocket_error", user_id=user_id, error=str(e))
        manager.disconnect(user_id, websocket)


# ── Root ───────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "KeepShot",
        "version": "1.0.0",
        "description": "AI-Powered Bookmark Monitoring System",
        "docs": "/docs",
        "health": "/health",
    }


# ── Routers ────────────────────────────────────────────────────────────────────
# Import after app creation to avoid circular imports.
from app.routers import bookmarks, notifications
from app.routers.auth import router as auth_router

app.include_router(auth_router, prefix="/api/v1")
app.include_router(bookmarks.router, prefix="/api/v1", tags=["Bookmarks"])
app.include_router(notifications.router, prefix="/api/v1", tags=["Notifications"])
