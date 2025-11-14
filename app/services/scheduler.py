"""Background scheduler for bookmark monitoring"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.bookmark import Bookmark
from app.services.monitor import monitor_bookmark
from app.core.logging import get_logger
from app.config import settings

logger = get_logger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def check_bookmarks_job():
    """
    Periodic job that checks all bookmarks that are due for monitoring.
    """
    db = SessionLocal()
    try:
        # Get all bookmarks with monitoring enabled that haven't been checked recently
        now = datetime.utcnow()

        bookmarks = db.query(Bookmark).filter(
            Bookmark.monitoring_enabled == True
        ).all()

        # Filter bookmarks that need checking based on their interval
        bookmarks_to_check = []
        for bm in bookmarks:
            if bm.last_checked_at is None:
                # Never checked - check it
                bookmarks_to_check.append(bm)
            else:
                # Check if enough time has passed
                time_since_check = (now - bm.last_checked_at).total_seconds() / 60  # minutes
                if time_since_check >= bm.check_interval:
                    bookmarks_to_check.append(bm)

        logger.info(
            "checking_bookmarks",
            total_bookmarks=len(bookmarks),
            bookmarks_to_check=len(bookmarks_to_check)
        )

        # Check bookmarks (limit concurrent checks)
        from asyncio import gather, Semaphore

        semaphore = Semaphore(settings.max_concurrent_checks)

        async def check_with_semaphore(bookmark):
            async with semaphore:
                try:
                    await monitor_bookmark(bookmark.id, db)
                except Exception as e:
                    logger.error(
                        "bookmark_check_failed",
                        bookmark_id=bookmark.id,
                        error=str(e)
                    )

        await gather(*[check_with_semaphore(bm) for bm in bookmarks_to_check])

        logger.info("bookmark_check_complete", checked=len(bookmarks_to_check))

    except Exception as e:
        logger.error("check_bookmarks_job_failed", error=str(e))
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler"""
    # Add the bookmark checking job (runs every 5 minutes)
    scheduler.add_job(
        check_bookmarks_job,
        trigger=IntervalTrigger(minutes=5),
        id="check_bookmarks",
        name="Check bookmarks for changes",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("scheduler_started")


def stop_scheduler():
    """Stop the background scheduler"""
    scheduler.shutdown()
    logger.info("scheduler_stopped")
