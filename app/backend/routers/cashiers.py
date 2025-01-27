from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.cashier_class import CashierClass

cashiers = APIRouter(
    prefix="/cashiers",
    tags=["Cashiers"]
)

@cashiers.get("/{branch_office_id}")
def index(branch_office_id:int, db: Session = Depends(get_db)):
    if branch_office_id != -1:
        data = CashierClass(db).get_all(branch_office_id)
    else:
        data = CashierClass(db).get_all()

    return {"message": data}

@cashiers.post("/all")
def all(db: Session = Depends(get_db)):
    data = CashierClass(db).get_all()

    return {"message": data}
