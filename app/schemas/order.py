from pydantic import BaseModel
from typing import List, Optional

class OrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float

    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    id: int
    status: str
    total: float
    items: List[OrderItemOut] = []

    class Config:
        from_attributes = True