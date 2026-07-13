from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.cart import CartItem
from app.models.order import Order
from app.models.notification import Notification
from app.models.event import UserEvent
from datetime import datetime, timedelta

ABANDON_THRESHOLD_MINUTES = 30  # cart abandoned after 30 mins

def detect_abandoned_carts(db: Session):
    """
    Find users who have items in cart
    but haven't ordered in 30 minutes.
    """
    threshold = datetime.utcnow() - timedelta(minutes=ABANDON_THRESHOLD_MINUTES)

    # Find users with old cart items
    abandoned = (
        db.query(CartItem.user_id, func.count(CartItem.id).label("items"))
        .filter(CartItem.added_at <= threshold)
        .group_by(CartItem.user_id)
        .all()
    )

    recovered = []

    for cart in abandoned:
        # Check if they already ordered recently
        recent_order = (
            db.query(Order)
            .filter(Order.user_id == cart.user_id)
            .filter(Order.created >= threshold)
            .first()
        )

        if recent_order:
            continue  # they ordered, not abandoned

        # Check if already notified
        already_notified = (
            db.query(Notification)
            .filter(Notification.user_id == cart.user_id)
            .filter(Notification.type == "abandoned_cart")
            .filter(Notification.created_at >= threshold)
            .first()
        )

        if already_notified:
            continue  # already sent notification

        # Create recovery notification
        notification = Notification(
            user_id=cart.user_id,
            message=f"You left {cart.items} item(s) in your cart! Complete your purchase before they sell out.",
            type="abandoned_cart",
            is_read=False
        )
        db.add(notification)

        # Log event
        event = UserEvent(
            user_id=cart.user_id,
            event_type="abandoned_cart",
            data=f"user_id:{cart.user_id},items:{cart.items}"
        )
        db.add(event)
        recovered.append(cart.user_id)

    db.commit()
    return {"detected": len(recovered), "user_ids": recovered}


def get_abandonment_stats(db: Session):
    """
    Get abandonment statistics.
    """
    total_abandoned = (
        db.query(func.count(Notification.id))
        .filter(Notification.type == "abandoned_cart")
        .scalar()
    )

    total_orders = db.query(func.count(Order.id)).scalar()

    return {
        "total_abandoned_carts": total_abandoned,
        "total_orders": total_orders,
        "recovery_opportunity": total_abandoned
    }