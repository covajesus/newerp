from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.product_class import ProductClass

products = APIRouter(
    prefix="/products",
    tags=["Products"]
)

@products.get("/list")
def list(db: Session = Depends(get_db)):
    data = ProductClass(db).get_list()

    return {"message": data}