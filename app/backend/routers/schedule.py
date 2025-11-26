from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin
from app.backend.classes.schedule_class import ScheduleClass
from app.backend.schemas import CreateSchedule
from app.backend.auth.auth_user import get_current_active_user

schedule = APIRouter(
    prefix="/schedule",
    tags=["Schedule"]
)

@schedule.post("/store")
def store(data:CreateSchedule, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    print(data.horary_name)
    data = ScheduleClass(db).store(data)

    return {"message": data}

@schedule.get("/edit/{employee_type_id}/{group_id}/{search_term}")
def edit(employee_type_id:int, group_id:int, search_term:str = None, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ScheduleClass(db).get(employee_type_id, group_id, search_term)

    return {"message": data}

@schedule.get("/get_all")
def get_all(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ScheduleClass(db).get_all()

    return {"message": data}
