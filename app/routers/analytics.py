from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.event import UserEvent
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.cart import CartItem
from app.models.user import User
from app.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Total revenue
@router.get("/revenue")
def total_revenue(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = db.query(func.sum(Order.total)).filter(Order.status == "confirmed").scalar()
    return {"total_revenue": result or 0}

# Top products by views
@router.get("/top-products")
def top_products(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    results = (
        db.query(UserEvent.data, func.count(UserEvent.id).label("views"))
        .filter(UserEvent.event_type == "view_product")
        .group_by(UserEvent.data)
        .order_by(func.count(UserEvent.id).desc())
        .limit(10)
        .all()
    )
    return [{"product": r.data, "views": r.views} for r in results]

# Hourly activity
@router.get("/hourly-activity")
def hourly_activity(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    results = (
        db.query(
            func.hour(UserEvent.created_at).label("hour"),
            func.count(UserEvent.id).label("events")
        )
        .group_by(func.hour(UserEvent.created_at))
        .order_by(func.hour(UserEvent.created_at))
        .all()
    )
    return [{"hour": r.hour, "events": r.events} for r in results]

# Cart abandonment rate
@router.get("/cart-abandonment")
def cart_abandonment(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_carts = db.query(func.count(func.distinct(CartItem.user_id))).scalar()
    total_orders = db.query(func.count(func.distinct(Order.user_id))).scalar()
    abandoned = total_carts - total_orders
    rate = (abandoned / total_carts * 100) if total_carts > 0 else 0
    return {
        "total_carts": total_carts,
        "converted_to_order": total_orders,
        "abandoned": abandoned,
        "abandonment_rate": f"{rate:.1f}%"
    }

# Top search terms
@router.get("/search-terms")
def search_terms(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    results = (
        db.query(UserEvent.data, func.count(UserEvent.id).label("count"))
        .filter(UserEvent.event_type == "search")
        .group_by(UserEvent.data)
        .order_by(func.count(UserEvent.id).desc())
        .limit(10)
        .all()
    )
    return [{"term": r.data, "count": r.count} for r in results]

# Total users
@router.get("/users")
def total_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    count = db.query(func.count(User.id)).scalar()
    return {"total_users": count}
from app.abandoned_cart import detect_abandoned_carts, get_abandonment_stats

# Detect abandoned carts — run this periodically
@router.post("/detect-abandoned-carts")
def detect_abandoned(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = detect_abandoned_carts(db)
    return result

# Abandonment stats
@router.get("/abandonment-stats")
def abandonment_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_abandonment_stats(db)