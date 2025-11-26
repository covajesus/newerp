from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin
from app.backend.classes.regime_class import RegimeClass
from app.backend.auth.auth_user import get_current_active_user

regimes = APIRouter(
    prefix="/regimes",
    tags=["Regimes"]
)

@regimes.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = RegimeClass(db).get_all()

    return {"message": data}