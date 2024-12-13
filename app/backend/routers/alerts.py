from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Alert, UpdateAlert, UserLogin, AlertList
from app.backend.classes.alert_class import AlertClass
from app.backend.auth.auth_user import get_current_active_user

alerts = APIRouter(
    prefix="/alerts",
    tags=["Alert"]
)

@alerts.post("/")
def index(alert: AlertList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AlertClass(db).get_all(alert.rut, alert.page)
    
    return {"message": data}

@alerts.post("/store")
def store(alert:Alert, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    alert_inputs = alert.dict()

    data = AlertClass(db).store(alert_inputs)

    return {"message": data}

@alerts.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AlertClass(db).get("id", id)

    return {"message": data}

@alerts.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AlertClass(db).delete(id)

    return {"message": data}

@alerts.patch("/update/{id}")
def update(id: int, alert: UpdateAlert, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    alert_inputs = alert.dict()

    data = AlertClass(db).update(id, alert_inputs)

    return {"message": data}