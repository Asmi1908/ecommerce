from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime
from app.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id"))
    message    = Column(String(500))
    type       = Column(String(50), default="info")
    is_read    = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())