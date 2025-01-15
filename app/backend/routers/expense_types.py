from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.expense_type_class import ExpenseTypeClass

expense_types = APIRouter(
    prefix="/expense_types",
    tags=["ExpenseTypes"]
)

@expense_types.get("/")
def index(db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).get_all()

    return {"message": data}