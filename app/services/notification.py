"""Notification service — WebSocket push + optional webhook delivery"""
import hashlib
import hmac
import json

import httpx

from app.config import settings
from app.core.logging import get_logger
from app.models.notification import Notification

logger = get_logger(__name__)


async def send_notification(user_id: str, notification: Notification):
    """
    Deliver a notification through every configured channel:
      1. WebSocket  — real-time push to any connected browser/client
      2. Webhook    — HTTP POST to WEBHOOK_URL (if configured)
    """
    await _send_websocket(user_id, notification)
    await _send_webhook(notification)


# ── WebSocket ──────────────────────────────────────────────────────────────────

async def _send_websocket(user_id: str, notification: Notification):
    try:
        from app.main import manager  # local import to avoid circular

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
            },
        }

        await manager.send_personal_message(user_id, message)
        logger.info("websocket_notification_sent", user_id=user_id, notification_id=notification.id)

    except Exception as exc:
        logger.error("websocket_notification_failed", user_id=user_id, error=str(exc))


# ── Webhook ────────────────────────────────────────────────────────────────────

async def _send_webhook(notification: Notification):
    """
    POST the notification payload to WEBHOOK_URL.

    If WEBHOOK_SECRET is set the request includes:
      X-Keepshot-Signature: sha256=<hmac-sha256 of the raw JSON body>

    Receivers can verify authenticity by recomputing the HMAC with their
    copy of WEBHOOK_SECRET and comparing against this header.
    Webhook failures are logged but never propagate — they never crash the
    monitoring pipeline.
    """
    if not settings.webhook_url:
        return

    payload = {
        "event": "notification.created",
        "notification_id": notification.id,
        "user_id": notification.user_id,
        "bookmark_id": notification.bookmark_id,
        "type": notification.notification_type,
        "title": notification.title,
        "message": notification.message,
        "created_at": notification.created_at.isoformat(),
    }

    body = json.dumps(payload, separators=(",", ":"))
    headers = {"Content-Type": "application/json", "User-Agent": "Keepshot/1.0"}

    if settings.webhook_secret:
        sig = hmac.new(settings.webhook_secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        headers["X-Keepshot-Signature"] = f"sha256={sig}"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(settings.webhook_url, content=body, headers=headers)
            resp.raise_for_status()
        logger.info(
            "webhook_delivered",
            url=settings.webhook_url,
            notification_id=notification.id,
            status=resp.status_code,
        )
    except Exception as exc:
        logger.error("webhook_delivery_failed", url=settings.webhook_url, error=str(exc))
