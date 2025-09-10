from fastapi import APIRouter, Depends, Form, Query, Request
from app.backend.db.database import get_db
from app.backend.classes.kardex_value_class import KardexValueClass
from app.backend.schemas import KardexValueDatum, UpdateKardexValue, KardexRequest, KardexSearchRequest
from sqlalchemy.orm import Session

kardex_values = APIRouter(
    prefix="/kardex_values",
    tags=["KardexValues"]
)

@kardex_values.post("/")
async def index(
    data: KardexRequest,
    session: Session = Depends(get_db)
):
    kardex_class = KardexValueClass(session)
    result = kardex_class.get_all(
        page=data.page,
        items_per_page=10,
        code=None,
        product_id=None
    )
    
    # Formatear respuesta para coincidir con el frontend
    if isinstance(result, dict) and result.get("status") == "success":
        response_data = {
            "data": result.get("data", []),
            "total_items": result.get("total_items", 0),
            "items_per_page": 10,
            "current_page": result.get("current_page", 1)
        }
        return {"message": response_data}
    else:
        return {"message": {"data": [], "total_items": 0, "items_per_page": 10, "current_page": 1}}

@kardex_values.post("/search")
async def search_kardex_data(
    request: Request,
    data: KardexSearchRequest,
    session: Session = Depends(get_db)
):
    """
    Buscar en los datos del kardex con filtros
    """
    kardex_class = KardexValueClass(session)
    result = kardex_class.get_kardex_movements(
        page=data.page,
        items_per_page=10,
        code=data.code,
        product_id=data.product_id
    )
    
    # Formatear respuesta para coincidir con el frontend
    if isinstance(result, dict) and result.get("status") == "success":
        response_data = {
            "data": result.get("data", []),
            "total_items": result.get("total_items", 0),
            "items_per_page": 10,
            "current_page": result.get("current_page", 1)
        }
        return {"message": response_data}
    else:
        return {"message": {"data": [], "total_items": 0, "items_per_page": 10, "current_page": 1}}

