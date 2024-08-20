from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import AlertType, UpdateAlertType, UserLogin
from app.backend.classes.alert_type_class import AlertTypeClass
from app.backend.auth.auth_user import get_current_active_user

alert_types = APIRouter(
    prefix="/alert_types",
    tags=["AlertType"]
)

@alert_types.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AlertTypeClass(db).get_all()

    return {"message": data}

@alert_types.post("/store")
def store(alert_type:AlertType, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    alert_type_inputs = alert_type.dict()
    data = AlertTypeClass(db).store(alert_type_inputs)

    return {"message": data}

@alert_types.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AlertTypeClass(db).get("id", id)

    return {"message": data}

@alert_types.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AlertTypeClass(db).delete(id)

    return {"message": data}

@alert_types.patch("/update/{id}")
def update(id: int, alert_type: UpdateAlertType, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AlertTypeClass(db).update(id, alert_type)

    return {"message": data}