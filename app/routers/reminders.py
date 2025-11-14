class Reminder(Base):
    id: int
    user_id: int
    bookmark_id: int
    watchpoint_id: int
    type: str               # event / time / decay
    message: str
    status: str             # pending / resolved / snoozed
    created_at: datetime