from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.customer_class import CustomerClass

supervisors = APIRouter(
    prefix="/supervisors",
    tags=["Supervisor"]
)

@supervisors.post("/")
def index(db: Session = Depends(get_db)):

    data = CustomerClass(db).get_all()

    return {"message": data}