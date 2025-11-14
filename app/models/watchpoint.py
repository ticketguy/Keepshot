"""WatchPoint model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class WatchPoint(Base):
    """
    WatchPoint model - AI-extracted key fields to monitor for changes.
    Examples: price, availability, title, status, etc.
    """
    __tablename__ = "watchpoints"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    snapshot_id = Column(String, ForeignKey("snapshots.id"), nullable=False, index=True)

    # Field information
    field_name = Column(String, nullable=False)  # e.g., "price", "title", "availability"
    field_value = Column(Text, nullable=False)  # Current value
    field_type = Column(String, nullable=True)  # e.g., "currency", "string", "number"

    # Priority
    is_primary = Column(Boolean, default=False, nullable=False)  # Main field to monitor

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    snapshot = relationship("Snapshot", back_populates="watchpoints")
    changes = relationship("Change", back_populates="watchpoint", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WatchPoint(id='{self.id}', field='{self.field_name}', value='{self.field_value[:50]}')>"
