from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Health, UpdateHealth, UserLogin
from app.backend.classes.health_class import HealthClass
from app.backend.auth.auth_user import get_current_active_user

healths = APIRouter(
    prefix="/healths",
    tags=["Healths"]
)

@healths.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = HealthClass(db).get_all()

    return {"message": data}

@healths.post("/store")
def store(health:Health, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    health_inputs = health.dict()
    data = HealthClass(db).store(health_inputs)

    return {"message": data}

@healths.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = HealthClass(db).get("id", id)

    return {"message": data}

@healths.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = HealthClass(db).delete(id)

    return {"message": data}

@healths.patch("/update/{id}")
def update(id: int, health: UpdateHealth, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = HealthClass(db).update(id, health)

    return {"message": data}