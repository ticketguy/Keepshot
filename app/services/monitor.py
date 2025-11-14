"""Bookmark monitoring and change detection service"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models import Bookmark, Snapshot, WatchPoint, Change, Notification, NotificationType
from app.services.scraper import scraper
from app.services.ai import ai_service
from app.services.notification import send_notification
from app.core.logging import get_logger

logger = get_logger(__name__)


async def monitor_bookmark(bookmark_id: str, db: Session):
    """
    Monitor a bookmark for changes.

    1. Fetch current content
    2. Create new snapshot
    3. Compare with last snapshot
    4. Detect changes in watchpoints
    5. Analyze significance
    6. Create notifications if needed
    """
    try:
        bookmark = db.query(Bookmark).filter(Bookmark.id == bookmark_id).first()
        if not bookmark:
            logger.error("bookmark_not_found", bookmark_id=bookmark_id)
            return

        logger.info("monitoring_bookmark", bookmark_id=bookmark_id, title=bookmark.title)

        # Fetch current content
        scraped_data = await scraper.scrape(
            content_type=bookmark.content_type,
            url=bookmark.url,
            raw_content=bookmark.raw_content
        )

        # Get the last snapshot for comparison
        last_snapshot = (
            db.query(Snapshot)
            .filter(Snapshot.bookmark_id == bookmark_id)
            .order_by(Snapshot.created_at.desc())
            .first()
        )

        # Check if content has changed
        if last_snapshot and last_snapshot.content_hash == scraped_data["content_hash"]:
            # No change detected
            logger.info("no_change_detected", bookmark_id=bookmark_id)
            bookmark.last_checked_at = datetime.utcnow()
            db.commit()
            return

        logger.info("change_detected", bookmark_id=bookmark_id)

        # Create new snapshot
        new_snapshot = Snapshot(
            bookmark_id=bookmark_id,
            content_hash=scraped_data["content_hash"],
            extracted_content=scraped_data["content"],
            snapshot_data=scraped_data["metadata"]
        )
        db.add(new_snapshot)
        db.commit()
        db.refresh(new_snapshot)

        # Extract watchpoints from new snapshot
        watchpoints_data = await ai_service.extract_watchpoints(
            content=scraped_data["content"],
            content_type=bookmark.content_type,
            metadata=scraped_data["metadata"]
        )

        # Create watchpoint records
        new_watchpoints = []
        for wp_data in watchpoints_data:
            wp = WatchPoint(
                snapshot_id=new_snapshot.id,
                field_name=wp_data["field_name"],
                field_value=wp_data["field_value"],
                field_type=wp_data.get("field_type"),
                is_primary=wp_data.get("is_primary", False)
            )
            db.add(wp)
            new_watchpoints.append((wp, wp_data))

        db.commit()

        # If this is the first snapshot, no comparison needed
        if not last_snapshot:
            logger.info("first_snapshot_created", bookmark_id=bookmark_id)
            bookmark.last_checked_at = datetime.utcnow()
            db.commit()
            return

        # Compare watchpoints with last snapshot
        last_watchpoints = db.query(WatchPoint).filter(
            WatchPoint.snapshot_id == last_snapshot.id
        ).all()

        # Build lookup for old watchpoints
        old_watchpoints_map = {wp.field_name: wp for wp in last_watchpoints}

        # Detect changes
        changes_detected = []

        for new_wp, wp_data in new_watchpoints:
            old_wp = old_watchpoints_map.get(new_wp.field_name)

            if old_wp and old_wp.field_value != new_wp.field_value:
                # Analyze significance
                analysis = await ai_service.analyze_change_significance(
                    field_name=new_wp.field_name,
                    old_value=old_wp.field_value,
                    new_value=new_wp.field_value,
                    content_type=bookmark.content_type
                )

                # Create change record
                change = Change(
                    watchpoint_id=new_wp.id,
                    old_value=old_wp.field_value,
                    new_value=new_wp.field_value,
                    change_type=analysis.get("change_type", "modified"),
                    significance_score=analysis.get("significance_score", 0.5)
                )
                db.add(change)
                db.commit()
                db.refresh(change)

                changes_detected.append({
                    "field_name": new_wp.field_name,
                    "old_value": old_wp.field_value,
                    "new_value": new_wp.field_value,
                    "change_type": change.change_type,
                    "significance_score": change.significance_score,
                    "change_id": change.id
                })

                logger.info(
                    "change_recorded",
                    bookmark_id=bookmark_id,
                    field=new_wp.field_name,
                    significance=change.significance_score
                )

        # If significant changes detected, create notification
        if changes_detected:
            # Filter for significant changes (score >= 0.5)
            significant_changes = [c for c in changes_detected if c["significance_score"] >= 0.5]

            if significant_changes:
                # Generate notification message
                notification_data = await ai_service.generate_notification_message(
                    bookmark_title=bookmark.title or bookmark.url or "Your bookmark",
                    changes=significant_changes,
                    content_type=bookmark.content_type
                )

                # Create notification
                notification = Notification(
                    user_id=bookmark.user_id,
                    bookmark_id=bookmark.id,
                    change_id=significant_changes[0]["change_id"],  # Link to primary change
                    notification_type=NotificationType.CHANGE,
                    title=notification_data["title"],
                    message=notification_data["message"],
                    read=False
                )
                db.add(notification)
                db.commit()
                db.refresh(notification)

                # Send notification via WebSocket
                await send_notification(bookmark.user_id, notification)

                logger.info(
                    "notification_created",
                    bookmark_id=bookmark_id,
                    notification_id=notification.id,
                    changes_count=len(significant_changes)
                )

        # Update last checked timestamp
        bookmark.last_checked_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        logger.error("monitor_bookmark_failed", bookmark_id=bookmark_id, error=str(e))
        db.rollback()
        raise
