from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from ..database import Base

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    bookmark_id = Column(Integer, ForeignKey("bookmarks.id"))
    watchpoint_id = Column(Integer, ForeignKey("watchpoints.id"), nullable=True)
    type = Column(String, default="event")  # event / relevance / time
    message = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending / resolved / dismissed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())