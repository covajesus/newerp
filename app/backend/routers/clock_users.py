from fastapi import APIRouter, Depends, Request
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import ClockUser, UserLogin, UpdateClockUser
from app.backend.classes.clock_user_class import ClockUserClass
from app.backend.auth.auth_user import get_current_active_user

clock_users = APIRouter(
    prefix="/clock_users",
    tags=["ClockUsers"]
)

@clock_users.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ClockUserClass(db).get_all()

    return {"message": data}

@clock_users.post("/store")
def store(clock_user:ClockUser, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    clock_user_inputs = clock_user.dict()
    data = ClockUserClass(db).store(clock_user_inputs)

    return {"message": data}

@clock_users.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ClockUserClass(db).get("rut", id)

    return {"message": data}

@clock_users.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ClockUserClass(db).delete(id)

    return {"message": data}

@clock_users.patch("/update/{id}")
def update(id: int, clock_user: UpdateClockUser, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    clock_user_inputs = clock_user.dict()
    data = ClockUserClass(db).update(id, clock_user_inputs)

    return {"message": data}