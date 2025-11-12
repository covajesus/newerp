from fastapi import APIRouter, Depends, HTTPException
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Honorary, UpdateHonorary, UserLogin, HonoraryList, ValidateHonoraryRut, ImputeHonorary
from app.backend.classes.honorary_class import HonoraryClass
from app.backend.auth.auth_user import get_current_active_user

honoraries = APIRouter(
    prefix="/honoraries",
    tags=["Honoraries"]
)

@honoraries.post("/")
def index(honorary: HonoraryList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    print(session_user.rol_id)
    data = HonoraryClass(db).get_all(honorary.branch_office_id, honorary.rut, honorary.period, session_user.rut, session_user.rol_id, honorary.page)

    return {"message": data}

@honoraries.post("/store")
def store(form_data: Honorary = Depends(Honorary.as_form), session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = HonoraryClass(db).store(session_user.rut, form_data)

    return {"message": data}

@honoraries.post("/generate/{id}")
def generate(id: int, form_data: Honorary = Depends(Honorary.as_form), session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = HonoraryClass(db).generate(id, form_data)
    
    # Si el resultado es un dict con success=False, lanzar error HTTP
    if isinstance(data, dict) and not data.get("success", True):
        raise HTTPException(status_code=500, detail=data)

    return {"message": data}

@honoraries.post("/validate")
def validate(form_data: ValidateHonoraryRut = Depends(ValidateHonoraryRut.as_form), db: Session = Depends(get_db)):
    data = HonoraryClass(db).validate(form_data)

    return {"message": data} 

@honoraries.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = HonoraryClass(db).get("id", id)

    return {"message": data}

@honoraries.post("/impute")
def impute(form_data: ImputeHonorary = Depends(ImputeHonorary.as_form), session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = HonoraryClass(db).impute(form_data)

    return {"message": data}

@honoraries.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = HonoraryClass(db).delete(id)

    return {"message": data}

@honoraries.patch("/update/{id}")
def update(id: int, honorary: UpdateHonorary, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # Actualizar el honorario
    result = HonoraryClass(db).update(id, honorary)
    
    if result == 1:
        # Si el update fue exitoso y tiene foreigner_id == 1, emitir boleta
        if honorary.foreigner_id == 1 and honorary.status_id == 2:
            send_result = HonoraryClass(db).send(id, honorary)
            return {"message": send_result}
    
    return {"message": result}

@honoraries.get("/get_data_by_rut/{rut}")
def get_data_by_rut(rut: str, db: Session = Depends(get_db)):
    """
    Busca si el usuario con el RUT dado tiene boletas de honorarios 
    y devuelve la más próxima (próxima fecha de inicio)
    """
    data = HonoraryClass(db).get_data_by_rut(rut)
    return {"message": data}