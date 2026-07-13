from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductOut
from app.auth import get_current_user
from typing import List

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

# GET recommendations based on a product
@router.get("/product/{product_id}", response_model=List[ProductOut])
def product_recommendations(
    product_id: int,
    db: Session = Depends(get_db)
):
    # Find all orders that contain this product
    orders_with_product = (
        db.query(OrderItem.order_id)
        .filter(OrderItem.product_id == product_id)
        .subquery()
    )

    # Find other products bought in those same orders
    recommended_ids = (
        db.query(OrderItem.product_id, func.count(OrderItem.id).label("freq"))
        .filter(OrderItem.order_id.in_(orders_with_product))
        .filter(OrderItem.product_id != product_id)
        .group_by(OrderItem.product_id)
        .order_by(func.count(OrderItem.id).desc())
        .limit(5)
        .all()
    )

    if not recommended_ids:
        # Fallback — return products from same category
        source = db.query(Product).filter(Product.id == product_id).first()
        if not source:
            raise HTTPException(status_code=404, detail="Product not found")
        return (
            db.query(Product)
            .filter(Product.category == source.category)
            .filter(Product.id != product_id)
            .limit(5)
            .all()
        )

    ids = [r.product_id for r in recommended_ids]
    return db.query(Product).filter(Product.id.in_(ids)).all()


# GET personalized recommendations for logged in user
@router.get("/personal", response_model=List[ProductOut])
def personal_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Find products user has ordered
    ordered_ids = (
        db.query(OrderItem.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == current_user.id)
        .subquery()
    )

    # Find categories user likes
    liked_categories = (
        db.query(Product.category, func.count(Product.id).label("count"))
        .filter(Product.id.in_(ordered_ids))
        .group_by(Product.category)
        .order_by(func.count(Product.id).desc())
        .limit(3)
        .all()
    )

    if not liked_categories:
        # New user — return top selling products
        top_ids = (
            db.query(OrderItem.product_id, func.count(OrderItem.id).label("sales"))
            .group_by(OrderItem.product_id)
            .order_by(func.count(OrderItem.id).desc())
            .limit(5)
            .all()
        )
        ids = [r.product_id for r in top_ids]
        return db.query(Product).filter(Product.id.in_(ids)).all()

    # Return products from liked categories not yet ordered
    categories = [c.category for c in liked_categories]
    return (
        db.query(Product)
        .filter(Product.category.in_(categories))
        .filter(Product.id.notin_(ordered_ids))
        .limit(5)
        .all()
    )


# GET trending products
@router.get("/trending", response_model=List[ProductOut])
def trending_products(db: Session = Depends(get_db)):
    # Most ordered products overall
    top_ids = (
        db.query(OrderItem.product_id, func.count(OrderItem.id).label("sales"))
        .group_by(OrderItem.product_id)
        .order_by(func.count(OrderItem.id).desc())
        .limit(10)
        .all()
    )

    if not top_ids:
        return db.query(Product).limit(10).all()

    ids = [r.product_id for r in top_ids]
    return db.query(Product).filter(Product.id.in_(ids)).all()