"""FastAPI dependencies including auth middleware"""
from typing import Optional
from fastapi import Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User


async def get_current_user_id(
    x_user_id: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
) -> str:
    """
    Auth-agnostic user identification middleware.

    Builders can replace this with their own authentication logic:
    - JWT validation
    - OAuth token verification
    - API key lookup
    - Portid token validation
    - Session cookies
    - etc.

    For now, accepts user_id from header for simplicity.
    In production, this should validate tokens/credentials.
    """

    # Method 1: Direct user_id header (development/testing)
    if x_user_id:
        return x_user_id

    # Method 2: Bearer token (implement JWT/OAuth validation here)
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        # TODO: Validate token and extract user_id
        # For now, just use the token as user_id (NOT SECURE - EXAMPLE ONLY)
        return token

    # No authentication provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide X-User-Id header or Authorization token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    user_id: str = Header(None, alias="X-User-Id"),
    db: Session = None
) -> User:
    """
    Get the current authenticated user from database.
    Creates user if doesn't exist (for development ease).
    """
    if not db:
        db = next(get_db())

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        # Auto-create user for development
        # In production, this should be handled by signup flow
        user = User(id=user_id)
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


# Optional: JWT validation example (commented out)
"""
from datetime import datetime, timedelta
import jwt
from app.config import settings

def create_access_token(user_id: str) -> str:
    '''Create JWT access token'''
    expire = datetime.utcnow() + timedelta(seconds=settings.jwt_expiration)
    payload = {
        "user_id": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> str:
    '''Verify JWT token and return user_id'''
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(401, "Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.JWTError:
        raise HTTPException(401, "Invalid token")
"""


# Optional: Portid validation example (commented out)
"""
from harboria_portid import PortIDClient

portid_client = PortIDClient(
    app_id="your-app-id",
    sync_server_url="your-sync-server-url"
)

async def verify_portid_token(token: str) -> str:
    '''Verify Portid token and return user_id'''
    try:
        # Validate with Portid sync server
        user_data = await portid_client.verify_token(token)
        return user_data["user_id"]
    except Exception as e:
        raise HTTPException(401, f"Portid validation failed: {str(e)}")
"""
