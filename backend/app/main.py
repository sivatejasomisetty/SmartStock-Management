from fastapi import FastAPI, Body, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import pandas as pd

from app.database import engine
from app.auth import verify_firebase_token, require_role
from app.chatbot import chatbot_response
from app.ml.predictor import predict_units
from app.ml.alerts import generate_alerts

app = FastAPI(title="SmartStock Backend")

# -------------------- CORS --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- ROOT --------------------
@app.get("/")
def root():
    return {"status": "SmartStock Backend running"}

# -------------------- PRODUCTS --------------------

@app.get("/api/products/all")
def get_all_products(user=Depends(verify_firebase_token)):
    role = user.get("role")
    store_id = user.get("store_id")

    if role == "admin":
        query = "SELECT * FROM inventory_data LIMIT 2000"
        df = pd.read_sql(query, engine)

    elif role == "store_manager":
        query = """
            SELECT * FROM inventory_data
            WHERE store_id = :store_id
            LIMIT 2000
        """
        df = pd.read_sql(text(query), engine, params={"store_id": store_id})

    else:
        raise HTTPException(status_code=403, detail="Invalid role")

    df = df.where(pd.notnull(df), None)
    return {"products": df.to_dict(orient="records")}


@app.get("/api/products/{id}")
def get_product(id: int, user=Depends(verify_firebase_token)):
    role = user.get("role")
    store_id = user.get("store_id")

    query = "SELECT * FROM inventory_data WHERE id=:id"
    df = pd.read_sql(text(query), engine, params={"id": id})

    if df.empty:
        raise HTTPException(status_code=404, detail="Product not found")

    if role == "store_manager" and df.iloc[0]["store_id"] != store_id:
        raise HTTPException(status_code=403, detail="Not your store")

    return {"product": df.iloc[0].to_dict()}

# -------------------- ADMIN ONLY --------------------

@app.post("/api/products")
def add_product(product: dict = Body(...), user=Depends(require_role("admin"))):
    query = text("""
        INSERT INTO inventory_data
        (store_id, product_id, category, inventory_level, price)
        VALUES (:store_id, :product_id, :category, :inventory_level, :price)
    """)
    with engine.connect() as conn:
        conn.execute(query, product)
        conn.commit()
    return {"message": "Product added"}


@app.put("/api/products/{id}")
def update_product(
    id: int,
    product: dict = Body(...),
    user=Depends(require_role("admin"))
):
    query = text("""
        UPDATE inventory_data
        SET category=:category,
            inventory_level=:inventory_level,
            price=:price
        WHERE id=:id
    """)
    with engine.connect() as conn:
        conn.execute(query, {**product, "id": id})
        conn.commit()

    return {"message": "Product updated"}


@app.delete("/api/products/{id}")
def delete_product(id: int, user=Depends(require_role("admin"))):
    with engine.connect() as conn:
        conn.execute(
            text("DELETE FROM inventory_data WHERE id=:id"),
            {"id": id}
        )
        conn.commit()
    return {"message": "Product deleted"}

# -------------------- ML --------------------

@app.get("/predict")
def predict(store_id: str, product_id: str, user=Depends(verify_firebase_token)):
    return predict_units(store_id, product_id)


@app.get("/alerts")
def alerts(user=Depends(verify_firebase_token)):
    return generate_alerts()

# -------------------- CHATBOT --------------------

@app.post("/chat")
def chat(message: str = Body(..., embed=True), user=Depends(verify_firebase_token)):
    return {
        "reply": chatbot_response(message),
        "role": user.get("role"),
        "store_id": user.get("store_id")
    }
