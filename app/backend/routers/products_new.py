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
    """
    Obtener lista simple de productos para selects/combos
    """
    data = ProductClass(db).get_all(page=0)
    
    # Formatear datos para el frontend (solo id y name)
    if isinstance(data, list):
        # data es una lista directa de productos
        products_list = [
            {
                "id": product.get("product_id", product.get("id")), 
                "name": product.get("name", product.get("description", ""))
            } 
            for product in data
        ]
    elif isinstance(data, dict) and "data" in data:
        # data es un dict con estructura paginada
        products_list = [
            {
                "id": product.get("product_id", product.get("id")), 
                "name": product.get("name", product.get("description", ""))
            } 
            for product in data["data"]
        ]
    else:
        products_list = []
    
    return {"message": products_list}
