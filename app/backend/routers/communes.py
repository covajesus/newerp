from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Commune, UpdateCommune, UserLogin
from app.backend.classes.commune_class import CommuneClass
from app.backend.auth.auth_user import get_current_active_user

communes = APIRouter(
    prefix="/communes",
    tags=["Communes"]
)

@communes.get("/{region_id}")
def index(region_id:int, db: Session = Depends(get_db)):
    if region_id != -1:
        data = CommuneClass(db).get_all(region_id)
    else:
        data = CommuneClass(db).get_all()

    return {"message": data}

@communes.post("/store")
def store(commune:Commune, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    commune_inputs = commune.dict()
    data = CommuneClass(db).store(commune_inputs)

    return {"message": data}

@communes.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CommuneClass(db).get("id", id)

    return {"message": data}

@communes.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CommuneClass(db).delete(id)

    return {"message": data}

@communes.patch("/update/{id}")
def update(id: int, commune: UpdateCommune, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CommuneClass(db).update(id, commune)

    return {"message": data}