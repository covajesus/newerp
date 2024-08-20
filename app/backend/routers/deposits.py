from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin
from app.backend.classes.deposit_class import DepositClass
from app.backend.auth.auth_user import get_current_active_user

deposits = APIRouter(
    prefix="/deposits",
    tags=["Deposits"]
)

@deposits.get("/")
def index(db: Session = Depends(get_db)):
    data = DepositClass(db).get()

    return {"message": data}