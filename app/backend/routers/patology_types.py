from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import PatologyType, UpdatePatologyType, UserLogin
from app.backend.classes.patology_type_class import PatologyTypeClass
from app.backend.auth.auth_user import get_current_active_user

patology_types = APIRouter(
    prefix="/patology_types",
    tags=["PatologyTypes"]
)

@patology_types.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PatologyTypeClass(db).get_all()

    return {"message": data}

@patology_types.post("/store")
def store(patology_type:PatologyType, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    patology_type_inputs = patology_type.dict()
    data = PatologyTypeClass(db).store(patology_type_inputs)

    return {"message": data}

@patology_types.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PatologyTypeClass(db).get("id", id)

    return {"message": data}

@patology_types.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PatologyTypeClass(db).delete(id)

    return {"message": data}

@patology_types.patch("/update/{id}")
def update(id: int, patology_type: UpdatePatologyType, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PatologyTypeClass(db).update(id, patology_type)

    return {"message": data}