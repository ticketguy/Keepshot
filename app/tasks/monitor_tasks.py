from celery import Celery
from ..database import SessionLocal
from ..models import bookmark, watchpoint
from ..services.ai_parser import extract_watchpoints
from ..services.notifications import send_push_notification
import asyncio

celery = Celery("tasks", broker="redis://localhost:6379/0")

@celery.task
def monitor_bookmarks():
    db = SessionLocal()
    bookmarks = db.query(bookmark.Bookmark).all()

    for bm in bookmarks:
        content = "New fetched content"  # Replace with scraper
        watchpoints = asyncio.run(extract_watchpoints(content))

        for wp in watchpoints:
            db_wp = watchpoint.WatchPoint(
                snapshot_id=bm.id,
                field_name=wp["field_name"],
                value=wp["value"]
            )
            db.add(db_wp)
            db.commit()

            # Push notification
            asyncio.run(send_push_notification(bm.user_id, f"Bookmark {bm.url} updated!"))

    db.close()