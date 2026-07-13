from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.database import engine, Base
from app.models import user, product, order, event, cart, notification
from app.routers import products, auth
from app.routers import cart as cart_router
from app.routers import orders, search, analytics, recommendations, notifications
from app.exceptions import validation_exception_handler, general_exception_handler
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="E-Commerce API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    with open("app/static/dashboard.html", encoding="utf-8") as f:
        return f.read()
    
@app.get("/shop", response_class=HTMLResponse)
def shop():
    with open("app/static/index.html", encoding="utf-8") as f:
        return f.read()

@app.get("/product-page", response_class=HTMLResponse)
def product_page():
    with open("app/static/product.html", encoding="utf-8") as f:
        return f.read()

@app.get("/cart-page", response_class=HTMLResponse)
def cart_page():
    with open("app/static/cart.html", encoding="utf-8") as f:
        return f.read()

@app.get("/login-page", response_class=HTMLResponse)
def login_page():
    with open("app/static/login.html", encoding="utf-8") as f:
        return f.read()
    
# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart_router.router)
app.include_router(orders.router)
app.include_router(search.router)
app.include_router(analytics.router)
app.include_router(recommendations.router)
app.include_router(notifications.router)

@app.get("/")
def root():
    return {"message": "E-Commerce API running"}