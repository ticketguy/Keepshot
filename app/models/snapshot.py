from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from .database import Base

class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, index=True)
    bookmark_id = Column(Integer, ForeignKey("bookmarks.id"))
    snapshot_path = Column(String)           # optional full page capture
    content_summary = Column(String)         # AI-extracted summary
    created_at = Column(DateTime(timezone=True), server_default=func.now())