from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.cart import CartItem
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemOut
from app.auth import get_current_user
from typing import List

router = APIRouter(prefix="/cart", tags=["cart"])

# GET cart
@router.get("/", response_model=List[CartItemOut])
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(CartItem).filter(CartItem.user_id == current_user.id).all()

# POST add to cart
@router.post("/", response_model=CartItemOut)
def add_to_cart(
    data: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check product exists
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check stock
    if product.stock < data.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")

    # Check if already in cart
    existing = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == data.product_id
    ).first()

    if existing:
        existing.quantity += data.quantity
        db.commit()
        db.refresh(existing)
        return existing

    item = CartItem(
        user_id=current_user.id,
        product_id=data.product_id,
        quantity=data.quantity
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

# DELETE remove from cart
@router.delete("/{id}")
def remove_from_cart(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(CartItem).filter(
        CartItem.id == id,
        CartItem.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"deleted": id}