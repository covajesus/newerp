from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Honorary, UpdateHonorary, UserLogin, HonoraryList, GenerateHonorary
from app.backend.classes.honorary_class import HonoraryClass
from app.backend.auth.auth_user import get_current_active_user

honoraries = APIRouter(
    prefix="/honoraries",
    tags=["Honoraries"]
)

@honoraries.post("/")
def index(honorary: HonoraryList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = HonoraryClass(db).get_all(honorary.rut, honorary.rol_id, honorary.page)

    return {"message": data}

@honoraries.post("/store")
def store(honorary:Honorary, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    honorary_inputs = honorary.dict()
    data = HonoraryClass(db).store(honorary_inputs)

    return {"message": data}

@honoraries.post("/generate")
def generate(inputs:GenerateHonorary, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    honorary_inputs = inputs.dict()
    data = HonoraryClass(db).generate(honorary_inputs)

    return {"message": data}

@honoraries.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = HonoraryClass(db).get("id", id)

    return {"message": data}

@honoraries.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = HonoraryClass(db).delete(id)

    return {"message": data}

@honoraries.patch("/update/{id}")
def update(id: int, honorary: UpdateHonorary, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = HonoraryClass(db).update(id, honorary)

    if data == 1:
        data = HonoraryClass(db).send(honorary)

    return {"message": data}