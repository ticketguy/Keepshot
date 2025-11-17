"""Bookmarks API router"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.dependencies import get_current_user_id
from app.models import Bookmark, Snapshot, WatchPoint
from app.schemas.bookmark import (
    BookmarkCreate,
    BookmarkUpdate,
    BookmarkResponse,
    BookmarkListResponse,
)
from app.services.scraper import scraper
from app.services.ai import ai_service
from app.services.monitor import monitor_bookmark
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/bookmarks", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED)
async def create_bookmark(
    data: BookmarkCreate,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Create a new bookmark.

    This will:
    1. Scrape the content (if URL/image/video/PDF)
    2. Create initial snapshot
    3. Extract watchpoints using AI
    4. Schedule monitoring (if enabled)
    """
    try:
        logger.info("creating_bookmark", user_id=user_id, content_type=data.content_type)

        # Scrape content
        scraped_data = await scraper.scrape(
            content_type=data.content_type,
            url=data.url,
            raw_content=data.raw_content
        )

        # Create bookmark
        bookmark = Bookmark(
            user_id=user_id,
            content_type=data.content_type,
            url=data.url,
            title=data.title or scraped_data["metadata"].get("title"),
            description=data.description,
            raw_content=data.raw_content,
            file_path=scraped_data.get("file_path"),
            platform_data=data.platform_data or scraped_data["metadata"],
            monitoring_enabled=data.monitoring_enabled,
            check_interval=data.check_interval,
        )

        db.add(bookmark)
        db.commit()
        db.refresh(bookmark)

        # Create initial snapshot
        snapshot = Snapshot(
            bookmark_id=bookmark.id,
            content_hash=scraped_data["content_hash"],
            extracted_content=scraped_data["content"],
            snapshot_data=scraped_data["metadata"]
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        # Extract watchpoints
        watchpoints_data = await ai_service.extract_watchpoints(
            content=scraped_data["content"],
            content_type=bookmark.content_type,
            metadata=scraped_data["metadata"]
        )

        for wp_data in watchpoints_data:
            watchpoint = WatchPoint(
                snapshot_id=snapshot.id,
                field_name=wp_data["field_name"],
                field_value=wp_data["field_value"],
                field_type=wp_data.get("field_type"),
                is_primary=wp_data.get("is_primary", False)
            )
            db.add(watchpoint)

        db.commit()

        logger.info(
            "bookmark_created",
            bookmark_id=bookmark.id,
            watchpoints_count=len(watchpoints_data)
        )

        return bookmark

    except Exception as e:
        logger.error("bookmark_creation_failed", user_id=user_id, error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bookmark: {str(e)}"
        )


@router.get("/bookmarks", response_model=BookmarkListResponse)
async def list_bookmarks(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    monitoring_enabled: Optional[bool] = Query(None, description="Filter by monitoring status"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    List user's bookmarks with pagination.

    Supports filtering by content_type and monitoring_enabled.
    """
    query = db.query(Bookmark).filter(Bookmark.user_id == user_id)

    # Apply filters
    if content_type:
        query = query.filter(Bookmark.content_type == content_type)
    if monitoring_enabled is not None:
        query = query.filter(Bookmark.monitoring_enabled == monitoring_enabled)

    # Get total count
    total = query.count()

    # Apply pagination
    bookmarks = query.order_by(Bookmark.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return BookmarkListResponse(
        items=bookmarks,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get("/bookmarks/{bookmark_id}", response_model=BookmarkResponse)
async def get_bookmark(
    bookmark_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get a specific bookmark by ID."""
    bookmark = db.query(Bookmark).filter(
        Bookmark.id == bookmark_id,
        Bookmark.user_id == user_id
    ).first()

    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )

    return bookmark


@router.patch("/bookmarks/{bookmark_id}", response_model=BookmarkResponse)
async def update_bookmark(
    bookmark_id: str,
    data: BookmarkUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update a bookmark's settings."""
    bookmark = db.query(Bookmark).filter(
        Bookmark.id == bookmark_id,
        Bookmark.user_id == user_id
    ).first()

    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )

    # Update fields
    if data.title is not None:
        bookmark.title = data.title
    if data.description is not None:
        bookmark.description = data.description
    if data.monitoring_enabled is not None:
        bookmark.monitoring_enabled = data.monitoring_enabled
    if data.check_interval is not None:
        bookmark.check_interval = data.check_interval
    if data.platform_data is not None:
        bookmark.platform_data = data.platform_data

    db.commit()
    db.refresh(bookmark)

    logger.info("bookmark_updated", bookmark_id=bookmark_id)

    return bookmark


@router.delete("/bookmarks/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark(
    bookmark_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a bookmark and all associated data."""
    bookmark = db.query(Bookmark).filter(
        Bookmark.id == bookmark_id,
        Bookmark.user_id == user_id
    ).first()

    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )

    db.delete(bookmark)
    db.commit()

    logger.info("bookmark_deleted", bookmark_id=bookmark_id)


@router.post("/bookmarks/{bookmark_id}/check", status_code=status.HTTP_202_ACCEPTED)
async def trigger_bookmark_check(
    bookmark_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Trigger an immediate check of a bookmark.

    This bypasses the normal schedule and checks the bookmark right away.
    """
    bookmark = db.query(Bookmark).filter(
        Bookmark.id == bookmark_id,
        Bookmark.user_id == user_id
    ).first()

    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )

    # Add monitoring task to background
    background_tasks.add_task(monitor_bookmark, bookmark_id, db)

    logger.info("bookmark_check_triggered", bookmark_id=bookmark_id)

    return {"message": "Check triggered", "bookmark_id": bookmark_id}


@router.get("/bookmarks/{bookmark_id}/history")
async def get_bookmark_history(
    bookmark_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Get change history for a bookmark.

    Returns all snapshots and detected changes.
    """
    bookmark = db.query(Bookmark).filter(
        Bookmark.id == bookmark_id,
        Bookmark.user_id == user_id
    ).first()

    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )

    # Get all snapshots
    snapshots = db.query(Snapshot).filter(
        Snapshot.bookmark_id == bookmark_id
    ).order_by(Snapshot.created_at.desc()).all()

    # Build history
    history = []
    for snapshot in snapshots:
        watchpoints = db.query(WatchPoint).filter(
            WatchPoint.snapshot_id == snapshot.id
        ).all()

        history.append({
            "snapshot_id": snapshot.id,
            "created_at": snapshot.created_at.isoformat(),
            "content_hash": snapshot.content_hash,
            "watchpoints": [
                {
                    "field_name": wp.field_name,
                    "field_value": wp.field_value,
                    "field_type": wp.field_type,
                    "is_primary": wp.is_primary,
                }
                for wp in watchpoints
            ]
        })

    return {
        "bookmark_id": bookmark_id,
        "history": history
    }
