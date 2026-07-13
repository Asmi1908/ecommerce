from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Order(Base):
    __tablename__ = "orders"

    id       = Column(Integer, primary_key=True)
    user_id  = Column(Integer, ForeignKey("users.id"))
    status   = Column(String(50), default="pending")
    total    = Column(Float)
    created  = Column(DateTime, server_default=func.now())
    items    = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id         = Column(Integer, primary_key=True)
    order_id   = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity   = Column(Integer)
    price      = Column(Float)
    order      = relationship("Order", back_populates="items")