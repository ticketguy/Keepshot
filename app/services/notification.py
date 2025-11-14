"""Notification service for sending real-time notifications"""
from typing import Optional
from app.models.notification import Notification
from app.core.logging import get_logger

logger = get_logger(__name__)


async def send_notification(user_id: str, notification: Notification):
    """
    Send notification to user via WebSocket.

    This imports the connection manager from main.py to send
    notifications to connected WebSocket clients.
    """
    try:
        # Import here to avoid circular imports
        from app.main import manager

        message = {
            "type": "notification",
            "data": {
                "id": notification.id,
                "bookmark_id": notification.bookmark_id,
                "notification_type": notification.notification_type,
                "title": notification.title,
                "message": notification.message,
                "created_at": notification.created_at.isoformat(),
                "read": notification.read,
            }
        }

        await manager.send_personal_message(user_id, message)

        logger.info(
            "notification_sent",
            user_id=user_id,
            notification_id=notification.id
        )

    except Exception as e:
        logger.error(
            "notification_send_failed",
            user_id=user_id,
            notification_id=notification.id,
            error=str(e)
        )
