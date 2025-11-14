"""Main FastAPI application"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.logging import setup_logging, get_logger
from app.services.scheduler import start_scheduler, stop_scheduler

# Setup logging
setup_logging(debug=settings.debug)
logger = get_logger(__name__)

# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections for real-time notifications"""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        """Add a new WebSocket connection for a user"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info("websocket_connected", user_id=user_id)

    def disconnect(self, user_id: str, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info("websocket_disconnected", user_id=user_id)

    async def send_personal_message(self, user_id: str, message: dict):
        """Send message to all connections of a specific user"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error("websocket_send_failed", user_id=user_id, error=str(e))

    async def broadcast(self, message: dict):
        """Broadcast message to all connected users"""
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error("websocket_broadcast_failed", user_id=user_id, error=str(e))


# Global connection manager
manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("keepshot_starting", version="1.0.0")

    # Start background scheduler
    start_scheduler()
    logger.info("scheduler_started")

    yield

    # Cleanup
    stop_scheduler()
    logger.info("scheduler_stopped")
    logger.info("keepshot_shutdown")


# Create FastAPI app
app = FastAPI(
    title="KeepShot",
    description="AI-Powered Bookmark Monitoring System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Docker and monitoring"""
    return JSONResponse(
        content={
            "status": "healthy",
            "version": "1.0.0",
            "service": "keepshot"
        }
    )


# Metrics endpoint (placeholder)
@app.get("/metrics")
async def metrics():
    """Metrics endpoint for monitoring"""
    # TODO: Add Prometheus-compatible metrics
    return JSONResponse(
        content={
            "active_websockets": sum(len(conns) for conns in manager.active_connections.values()),
            "connected_users": len(manager.active_connections),
        }
    )


# WebSocket endpoint for real-time notifications
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for receiving real-time notifications.

    Connect to: ws://localhost:8000/ws/{your_user_id}

    Messages format:
    {
        "type": "notification",
        "data": {
            "id": "notification_id",
            "title": "Notification title",
            "message": "Notification message",
            "bookmark_id": "bookmark_id",
            "created_at": "2024-01-01T00:00:00Z"
        }
    }
    """
    await manager.connect(user_id, websocket)
    try:
        while True:
            # Keep connection alive and receive messages from client
            data = await websocket.receive_text()
            # Echo back for connection keep-alive
            await websocket.send_json({"type": "pong", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception as e:
        logger.error("websocket_error", user_id=user_id, error=str(e))
        manager.disconnect(user_id, websocket)


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "KeepShot",
        "version": "1.0.0",
        "description": "AI-Powered Bookmark Monitoring System",
        "docs": "/docs",
        "health": "/health",
    }


# Import and include routers (after app is created to avoid circular imports)
from app.routers import bookmarks, notifications

app.include_router(bookmarks.router, prefix="/api/v1", tags=["Bookmarks"])
app.include_router(notifications.router, prefix="/api/v1", tags=["Notifications"])
