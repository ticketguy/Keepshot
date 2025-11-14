from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from .database import Base

class WatchPoint(Base):
    __tablename__ = "watchpoints"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(Integer, ForeignKey("snapshots.id"))
    field_name = Column(String)              # e.g., price, text_block
    value = Column(String)
    last_checked = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="active") # active / changed / expired