from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(200), nullable=False)
    description = Column(Text)
    price       = Column(Float, nullable=False)
    stock       = Column(Integer, default=0)
    category    = Column(String(100))
    created     = Column(DateTime, server_default=func.now())