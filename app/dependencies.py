"""FastAPI dependencies including JWT auth middleware"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Header, HTTPException, status

from app.config import settings
from app.core import jwt as _jwt
from app.core.password import hash_password as _hash_password, verify_password as _verify_password


def get_password_hash(password: str) -> str:
    """Hash a plain-text password (PBKDF2-SHA256)."""
    return _hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a PBKDF2 hash."""
    return _verify_password(plain_password, hashed_password)


def create_access_token(user_id: str) -> str:
    """
    Create a signed HS256 JWT for the given user_id.

    Raises RuntimeError if JWT_SECRET is not configured.
    """
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET environment variable must be set to use token auth")

    expire = datetime.utcnow() + timedelta(seconds=settings.jwt_expiration)
    payload = {
        "sub": user_id,
        "exp": expire.timestamp(),
        "iat": datetime.utcnow().timestamp(),
    }
    return _jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode_token(token: str) -> str:
    """
    Decode and validate a JWT, returning the user_id ('sub' claim).

    Raises HTTP 401 on any validation failure.
    """
    if not settings.jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET is not configured on the server",
        )
    try:
        payload = _jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: Optional[str] = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: missing sub claim")
        return user_id
    except _jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except _jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_id(
    x_user_id: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
) -> str:
    """
    Resolve the authenticated user_id for a request.

    Primary method: Bearer JWT in the Authorization header.
    Fallback (DEBUG only): X-User-Id header for local development.
    """
    # Primary: validate Bearer JWT
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        return _decode_token(token)

    # Debug-only fallback: allow raw X-User-Id header
    if settings.debug and x_user_id:
        return x_user_id

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide 'Authorization: Bearer <token>'.",
        headers={"WWW-Authenticate": "Bearer"},
    )
