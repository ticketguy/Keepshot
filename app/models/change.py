"""Change model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Change(Base):
    """
    Change model - records detected changes in watchpoints.
    Stores what changed, how it changed, and AI-determined significance.
    """
    __tablename__ = "changes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    watchpoint_id = Column(String, ForeignKey("watchpoints.id"), nullable=False, index=True)

    # Change details
    old_value = Column(Text, nullable=False)
    new_value = Column(Text, nullable=False)
    change_type = Column(String, nullable=True)  # increase, decrease, modified, added, removed

    # AI-determined significance (0.0 to 1.0)
    significance_score = Column(Float, default=0.5, nullable=False)

    # Timestamp
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    watchpoint = relationship("WatchPoint", back_populates="changes")
    notifications = relationship("Notification", back_populates="change")

    def __repr__(self):
        return f"<Change(id='{self.id}', type='{self.change_type}', significance={self.significance_score})>"
