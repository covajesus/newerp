from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Gender, UpdateGender, UserLogin
from app.backend.classes.holiday_class import HolidayClass
from app.backend.auth.auth_user import get_current_active_user

holidays = APIRouter(
    prefix="/holidays",
    tags=["Holidays"]
)

@holidays.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = HolidayClass(db).get_all()

    return {"message": data}

@holidays.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = HolidayClass(db).get("id", id)

    return {"message": data}

