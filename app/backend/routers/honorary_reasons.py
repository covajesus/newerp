from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import  UserLogin
from app.backend.classes.honorary_reason_class import HonoraryReasonClass
from app.backend.auth.auth_user import get_current_active_user

honorary_reasons = APIRouter(
    prefix="/honorary_reasons",
    tags=["Honorary_Reasons"]
)

@honorary_reasons.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = HonoraryReasonClass(db).get_all()

    return {"message": data}