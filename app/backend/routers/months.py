from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.month_class import MonthClass

months = APIRouter(
    prefix="/months",
    tags=["Month"]
)

@months.get("/")
def index(db: Session = Depends(get_db)):
    data = MonthClass(db).get_all()

    return {"message": data}