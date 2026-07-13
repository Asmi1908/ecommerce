from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.product import Product
from app.models.user import User
from app.models.event import UserEvent
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut
from app.auth import get_current_user
from app.surge import get_surge_price
from typing import List, Optional
from app.cache import get_cache, set_cache, clear_product_cache

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db)):
    # Check cache first
    cached = get_cache("product:all")
    if cached:
        return cached

    # If not cached, get from DB
    products = db.query(Product).all()

    # Save to cache for 60 seconds
    result = []
    for p in products:
        result.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "stock": p.stock,
            "category": p.category
        })

    set_cache("product:all", result, ttl=60)
    return products

# GET single product with surge price — public
@router.get("/{id}")
def get_product(id: int, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")

    # Log view event
    event = UserEvent(
        user_id=None,
        event_type="view_product",
        data=f"product_id:{id}"
    )
    db.add(event)
    db.commit()

    # Get surge price
    surge_info = get_surge_price(p.price, id, db)

    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "category": p.category,
        "stock": p.stock,
        "base_price": p.price,
        "current_price": surge_info["surge_price"],
        "is_surging": surge_info["is_surging"],
        "surge_multiplier": surge_info["surge_multiplier"],
        "surge_percentage": surge_info["surge_percentage"]
    }

# POST create product — protected
@router.post("/", response_model=ProductOut)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    p = Product(**data.dict())
    db.add(p)
    db.commit()
    clear_product_cache()
    db.refresh(p)
    return p

# PUT update product — protected
@router.put("/{id}", response_model=ProductOut)
def update_product(
    id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    p = db.query(Product).filter(Product.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(p, key, value)
    db.commit()
    db.refresh(p)
    return p

# DELETE product — protected
@router.delete("/{id}")
def delete_product(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    p = db.query(Product).filter(Product.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(p)
    db.commit()
    clear_product_cache()
    return {"deleted": id}

# GET surge status for a product
@router.get("/{id}/surge")
def get_surge_status(id: int, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return get_surge_price(p.price, id, db)