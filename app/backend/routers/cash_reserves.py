from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.cash_reserve_class import CashReserveClass
from app.backend.schemas import CashReserve
from app.backend.schemas import CashReserveList
from fastapi import HTTPException
import json

cash_reserves = APIRouter(
    prefix="/cash_reserves",
    tags=["Cash_Reserves"]
)

@cash_reserves.post("/")
def index(cash_reserve: CashReserveList, db: Session = Depends(get_db)):
    data = CashReserveClass(db).get_all(cash_reserve.branch_office_id, cash_reserve.page)

    return {"message": data}

@cash_reserves.post("/store")
def store(
    form_data: CashReserve = Depends(CashReserve.as_form),
    db: Session = Depends(get_db)
):
    try:
        message = CashReserveClass(db).store(form_data)

        return {"message": message}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")

@cash_reserves.delete("/delete/{id}")
def delete(id:int, db: Session = Depends(get_db)):
    message = CashReserveClass(db).delete(id)

    return {"message": message}