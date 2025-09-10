from fastapi import APIRouter, Depends, HTTPException
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.movement_product_class import MovementProductClass
from app.backend.auth.auth_user import get_current_active_user

movement_products = APIRouter(
    prefix="/movement_products",
    tags=["Movement Products"]
)

@movement_products.get("/{movement_id}")
def show(movement_id: int, page: int = 1, items_per_page: int = 10, db: Session = Depends(get_db)):
    data = MovementProductClass(db).show(movement_id, page, items_per_page)
    
    return {"message": data}

@movement_products.get("/all/{movement_id}")
def get_all(movement_id: int, db: Session = Depends(get_db)):
    data = MovementProductClass(db).get_all(movement_id)
    
    return {"message": data}

@movement_products.get("/detail/{movement_product_id}")
def get_detail(movement_product_id: int, db: Session = Depends(get_db)):
    data = MovementProductClass(db).get(movement_product_id)
    
    return {"message": data}