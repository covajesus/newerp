from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Honorary, UpdateHonorary, UserLogin, HonoraryList, ValidateHonoraryRut
from app.backend.classes.honorary_class import HonoraryClass
from app.backend.auth.auth_user import get_current_active_user

honoraries = APIRouter(
    prefix="/honoraries",
    tags=["Honoraries"]
)

@honoraries.post("/")
def index(honorary: HonoraryList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = HonoraryClass(db).get_all(session_user.rut, session_user.rol_id, honorary.page)

    return {"message": data}

@honoraries.post("/store")
def store(form_data: Honorary = Depends(Honorary.as_form), session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = HonoraryClass(db).store(session_user.rut, form_data)

    return {"message": data}

@honoraries.post("/generate/{id}")
def generate(id: int, form_data: Honorary = Depends(Honorary.as_form), session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = HonoraryClass(db).generate(id, form_data)

    return {"message": data}

@honoraries.post("/validate")
def generate(form_data: ValidateHonoraryRut = Depends(ValidateHonoraryRut.as_form), db: Session = Depends(get_db)):
    data = HonoraryClass(db).validate(form_data)

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