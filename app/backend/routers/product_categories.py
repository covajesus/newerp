from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.product_category_class import ProductCategoryClass

product_categories = APIRouter(
    prefix="/product_categories",
    tags=["ProductCategories"]
)

@product_categories.get("/list")
def list(db: Session = Depends(get_db)):
    """
    Lista todos los product categories
    """
    data = ProductCategoryClass(db).get_all()
    return {"message": data}
