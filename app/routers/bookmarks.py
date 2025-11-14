from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import bookmark
from pydantic import BaseModel
from ..services.ai_parser import extract_watchpoints
import asyncio

router = APIRouter()

class BookmarkCreate(BaseModel):
    url: str
    title: str = None
    description: str = None
    type: str = None

@router.post("/bookmark")
async def create_bookmark(data: BookmarkCreate, db: Session = Depends(get_db)):
    new_bm = bookmark.Bookmark(
        user_id=1,
        url=data.url,
        title=data.title,
        description=data.description,
        type=data.type
    )
    db.add(new_bm)
    db.commit()
    db.refresh(new_bm)

    # Create initial snapshot (placeholder)
    snapshot_content = "Initial content of URL"  # Replace with actual scraper
    watchpoints = await extract_watchpoints(snapshot_content)

    # Save watchpoints (simplified)
    from ..models import watchpoint
    for wp in watchpoints:
        db_wp = watchpoint.WatchPoint(
            snapshot_id=new_bm.id,
            field_name=wp["field_name"],
            value=wp["value"]
        )
        db.add(db_wp)
    db.commit()
    
    return {"bookmark_id": new_bm.id, "message": "KeepShot saved with AI watchpoints!"}