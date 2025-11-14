"""Snapshot model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Snapshot(Base):
    """
    Snapshot model - stores content snapshots at different points in time.
    Used for change detection.
    """
    __tablename__ = "snapshots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    bookmark_id = Column(String, ForeignKey("bookmarks.id"), nullable=False, index=True)

    # Content data
    content_hash = Column(String, nullable=False)  # SHA256 hash for quick comparison
    extracted_content = Column(Text, nullable=True)  # Cleaned/processed content
    snapshot_data = Column(JSON, default=dict)  # Full snapshot data

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    bookmark = relationship("Bookmark", back_populates="snapshots")
    watchpoints = relationship("WatchPoint", back_populates="snapshot", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Snapshot(id='{self.id}', bookmark_id='{self.bookmark_id}')>"
