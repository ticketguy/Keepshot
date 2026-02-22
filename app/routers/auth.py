"""Auth router — register and login with JWT"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, TokenResponse
from app.dependencies import create_access_token, get_password_hash, verify_password
from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user account and return a JWT.

    Username must be unique. Password is stored as a bcrypt hash.
    """
    if not settings.jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET is not configured on the server",
        )

    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    user = User(
        id=str(uuid.uuid4()),
        username=data.username,
        password_hash=get_password_hash(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    logger.info("user_registered", user_id=user.id, username=user.username)

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        expires_in=settings.jwt_expiration,
    )


@router.post("/token", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Login with username + password (OAuth2 password flow) and return a JWT.

    Use the returned `access_token` in subsequent requests:
    `Authorization: Bearer <access_token>`
    """
    if not settings.jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET is not configured on the server",
        )

    user = db.query(User).filter(User.username == form.username).first()
    if not user or not user.password_hash or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user.id)
    logger.info("user_logged_in", user_id=user.id, username=user.username)

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        expires_in=settings.jwt_expiration,
    )
