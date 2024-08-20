from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Zone, UpdateZone, UserLogin
from app.backend.classes.zone_class import ZoneClass
from app.backend.auth.auth_user import get_current_active_user

zones = APIRouter(
    prefix="/zones",
    tags=["zones"]
)

@zones.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ZoneClass(db).get_all()

    return {"message": data}

@zones.post("/store")
def store(zone:Zone, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    zone_inputs = zone.dict()
    data = ZoneClass(db).store(zone_inputs)

    return {"message": data}

@zones.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ZoneClass(db).get("id", id)

    return {"message": data}

@zones.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ZoneClass(db).delete(id)

    return {"message": data}

@zones.patch("/update/{id}")
def update(id: int, zone: UpdateZone, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ZoneClass(db).update(id, zone)

    return {"message": data}