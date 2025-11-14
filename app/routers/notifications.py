"""Notifications API router"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id
from app.models import Notification
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationUpdate,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/notifications", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    read: Optional[bool] = Query(None, description="Filter by read status"),
    notification_type: Optional[str] = Query(None, description="Filter by type"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    List user's notifications with pagination.

    Supports filtering by read status and notification type.
    """
    query = db.query(Notification).filter(Notification.user_id == user_id)

    # Apply filters
    if read is not None:
        query = query.filter(Notification.read == read)
    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)

    # Get total count
    total = query.count()

    # Apply pagination
    notifications = query.order_by(Notification.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return NotificationListResponse(
        items=notifications,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get("/notifications/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get a specific notification by ID."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    return notification


@router.patch("/notifications/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: str,
    data: NotificationUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Mark notification as read/unread."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    notification.read = data.read
    db.commit()
    db.refresh(notification)

    logger.info("notification_updated", notification_id=notification_id, read=data.read)

    return notification


@router.delete("/notifications/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a notification."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    db.delete(notification)
    db.commit()

    logger.info("notification_deleted", notification_id=notification_id)


@router.post("/notifications/mark-all-read", status_code=status.HTTP_200_OK)
async def mark_all_read(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read for the current user."""
    count = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.read == False
    ).update({"read": True})

    db.commit()

    logger.info("marked_all_read", user_id=user_id, count=count)

    return {"message": f"Marked {count} notifications as read"}
