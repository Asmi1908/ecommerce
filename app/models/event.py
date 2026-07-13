from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class UserEvent(Base):
    __tablename__ = "user_events"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=True)
    event_type = Column(String(100))
    data  = Column(Text)
    created_at = Column(DateTime, server_default=func.now(), index=True)