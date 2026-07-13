from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.order import Order, OrderItem
from app.models.cart import CartItem
from app.models.product import Product
from app.models.user import User
from app.models.event import UserEvent
from app.schemas.order import OrderOut
from app.auth import get_current_user
from typing import List

router = APIRouter(prefix="/orders", tags=["orders"])

# POST place order from cart
@router.post("/", response_model=OrderOut)
def place_order(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get user's cart
    cart_items = db.query(CartItem).filter(
        CartItem.user_id == current_user.id
    ).all()

    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Calculate total
    total = 0
    order_items = []

    for item in cart_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Not enough stock for {product.name}")
        total += product.price * item.quantity
        order_items.append((product, item.quantity, product.price))

    # Create order
    order = Order(user_id=current_user.id, total=total, status="confirmed")
    db.add(order)
    db.commit()
    db.refresh(order)

    # Create order items and reduce stock
    for product, quantity, price in order_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            price=price
        )
        db.add(order_item)
        product.stock -= quantity

    # Clear cart
    for item in cart_items:
        db.delete(item)

    # Log event
    event = UserEvent(
        user_id=current_user.id,
        event_type="place_order",
        data=f"order_id:{order.id},total:{total}"
    )
    db.add(event)
    db.commit()
    db.refresh(order)
    return order

# GET order history
@router.get("/", response_model=List[OrderOut])
def get_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Order).filter(Order.user_id == current_user.id).all()

# GET single order
@router.get("/{id}", response_model=OrderOut)
def get_order(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(
        Order.id == id,
        Order.user_id == current_user.id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order