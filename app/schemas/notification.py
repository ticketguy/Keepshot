"""Pydantic schemas for Notification API"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.notification import NotificationType


class NotificationResponse(BaseModel):
    """Schema for notification response"""

    id: str
    user_id: str
    bookmark_id: str
    change_id: Optional[str]
    notification_type: NotificationType
    title: str
    message: str
    read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    """Schema for paginated notification list"""

    items: List[NotificationResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class NotificationUpdate(BaseModel):
    """Schema for updating a notification"""

    read: bool = Field(..., description="Mark notification as read/unread")
