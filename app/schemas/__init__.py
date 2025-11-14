"""Pydantic schemas for API validation"""
from app.schemas.bookmark import (
    BookmarkCreate,
    BookmarkUpdate,
    BookmarkResponse,
    BookmarkListResponse,
)
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationUpdate,
)

__all__ = [
    "BookmarkCreate",
    "BookmarkUpdate",
    "BookmarkResponse",
    "BookmarkListResponse",
    "NotificationResponse",
    "NotificationListResponse",
    "NotificationUpdate",
]
