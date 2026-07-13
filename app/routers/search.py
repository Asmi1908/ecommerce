from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.database import get_db
from app.models.product import Product
from app.models.event import UserEvent
from app.models.user import User
from app.schemas.product import ProductOut
from app.auth import get_current_user
from typing import List, Optional

router = APIRouter(prefix="/search", tags=["search"])

# Keyword mapping for smart search
SMART_KEYWORDS = {
    "warm": ["jacket", "sweater", "coat", "wool", "fleece", "winter"],
    "winter": ["jacket", "coat", "boots", "gloves", "sweater"],
    "summer": ["shorts", "tshirt", "sandals", "sunglasses", "dress"],
    "cool": ["tshirt", "shorts", "sandals", "casual"],
    "formal": ["shirt", "suit", "blazer", "trousers", "tie"],
    "cheap": ["budget", "affordable", "basic"],
    "premium": ["luxury", "premium", "branded", "designer"],
    "comfortable": ["casual", "cotton", "soft", "relaxed"],
    "running": ["shoes", "track", "sport", "athletic"],
    "gaming": ["laptop", "keyboard", "mouse", "headset", "monitor"],
    "fast": ["express", "quick", "speed"],
    "powerful": ["laptop", "processor", "performance", "pro"],
}

def expand_query(q: str) -> List[str]:
    """
    Expand search query with smart keywords.
    'warm' -> ['warm', 'jacket', 'sweater', 'coat'...]
    """
    terms = [q.lower()]
    words = q.lower().split()
    for word in words:
        if word in SMART_KEYWORDS:
            terms.extend(SMART_KEYWORDS[word])
    return list(set(terms))


# Smart search
@router.get("/", response_model=List[ProductOut])
def search_products(
    q: Optional[str] = Query(None, description="Search term"),
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    sort_by: Optional[str] = Query("newest", enum=["newest", "price_low", "price_high"]),
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    query = db.query(Product)

    if q:
        # Expand query with smart keywords
        expanded_terms = expand_query(q)

        # Build filter for all expanded terms
        filters = []
        for term in expanded_terms:
            filters.append(Product.name.ilike(f"%{term}%"))
            filters.append(Product.description.ilike(f"%{term}%"))
            filters.append(Product.category.ilike(f"%{term}%"))

        query = query.filter(or_(*filters))

        # Log search event
        event = UserEvent(
            user_id=None,
            event_type="search",
            data=f"query:{q},expanded:{','.join(expanded_terms)}"
        )
        db.add(event)
        db.commit()

    # Filter by category
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))

    # Filter by price
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # Sorting
    if sort_by == "price_low":
        query = query.order_by(Product.price.asc())
    elif sort_by == "price_high":
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.id.desc())

    # Pagination
    offset = (page - 1) * limit
    return query.offset(offset).limit(limit).all()


# Search suggestions based on popular terms
@router.get("/suggestions")
def search_suggestions(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    # Get popular searches matching the query
    popular = (
        db.query(UserEvent.data, func.count(UserEvent.id).label("count"))
        .filter(UserEvent.event_type == "search")
        .filter(UserEvent.data.ilike(f"%query:{q}%"))
        .group_by(UserEvent.data)
        .order_by(func.count(UserEvent.id).desc())
        .limit(5)
        .all()
    )

    # Extract just the query terms
    suggestions = []
    for p in popular:
        try:
            term = p.data.split("query:")[1].split(",")[0]
            if term not in suggestions:
                suggestions.append(term)
        except:
            pass

    # Also add smart keyword suggestions
    words = q.lower().split()
    for word in words:
        if word in SMART_KEYWORDS:
            suggestions.extend(SMART_KEYWORDS[word][:3])

    return {"query": q, "suggestions": list(set(suggestions))[:8]}


# Search history — personal
@router.get("/history")
def search_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    history = (
        db.query(UserEvent)
        .filter(UserEvent.user_id == current_user.id)
        .filter(UserEvent.event_type == "search")
        .order_by(UserEvent.created_at.desc())
        .limit(10)
        .all()
    )
    results = []
    for h in history:
        try:
            term = h.data.split("query:")[1].split(",")[0]
            results.append({
                "query": term,
                "searched_at": h.created_at
            })
        except:
            pass
    return results