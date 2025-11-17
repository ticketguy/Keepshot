"""Bookmark model"""
import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ContentType(str, enum.Enum):
    """Content types supported by KeepShot"""
    URL = "url"
    IMAGE = "image"
    VIDEO = "video"
    PDF = "pdf"
    TEXT = "text"


class Bookmark(Base):
    """
    Bookmark model - stores user's saved content.
    Supports multiple content types (URLs, images, videos, PDFs, text).
    """
    __tablename__ = "bookmarks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Content information
    content_type = Column(Enum(ContentType), nullable=False)
    url = Column(Text, nullable=True)  # Nullable for text snippets
    title = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    raw_content = Column(Text, nullable=True)  # For text snippets
    file_path = Column(Text, nullable=True)  # For downloaded files

    # Platform-specific data (renamed from metadata to avoid SQLAlchemy conflict)
    # Example: {"tweet_id": "123", "author": "@user", "likes": 100}
    platform_data = Column(JSON, default=dict)

    # Monitoring configuration
    monitoring_enabled = Column(Boolean, default=True, nullable=False)
    check_interval = Column(Integer, default=60, nullable=False)  # minutes

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_checked_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="bookmarks")
    snapshots = relationship("Snapshot", back_populates="bookmark", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="bookmark", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Bookmark(id='{self.id}', type='{self.content_type}', title='{self.title}')>"
