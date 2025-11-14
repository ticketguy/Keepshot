"""Notification model"""
import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class NotificationType(str, enum.Enum):
    """Notification types"""
    CHANGE = "change"  # Content changed
    DUPLICATE = "duplicate"  # Duplicate bookmark detected
    RELATED = "related"  # Related bookmark found
    REMINDER = "reminder"  # Generic reminder


class Notification(Base):
    """
    Notification model - stores user notifications.
    Generated when significant changes are detected or related content is found.
    """
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    bookmark_id = Column(String, ForeignKey("bookmarks.id"), nullable=False, index=True)
    change_id = Column(String, ForeignKey("changes.id"), nullable=True, index=True)

    # Notification content
    notification_type = Column(Enum(NotificationType), nullable=False)
    title = Column(Text, nullable=False)
    message = Column(Text, nullable=False)

    # Status
    read = Column(Boolean, default=False, nullable=False)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="notifications")
    bookmark = relationship("Bookmark", back_populates="notifications")
    change = relationship("Change", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(id='{self.id}', type='{self.notification_type}', read={self.read})>"
