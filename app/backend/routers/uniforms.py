from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Uniform, UpdateUniform, UserLogin
from app.backend.classes.uniform_class import UniformClass
from app.backend.auth.auth_user import get_current_active_user

uniforms = APIRouter(
    prefix="/uniforms",
    tags=["Uniform"]
)

@uniforms.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = UniformClass(db).get_all()

    return {"message": data}

@uniforms.post("/store")
def store(uniform:Uniform, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    uniform_inputs = uniform.dict()
    data = UniformClass(db).store(uniform_inputs)

    return {"message": data}

@uniforms.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = UniformClass(db).get("rut", id)

    return {"message": data}

@uniforms.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = UniformClass(db).delete(id)

    return {"message": data}

@uniforms.patch("/update/{id}")
def update(id: int, uniform: UpdateUniform, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = UniformClass(db).update(id, uniform)

    return {"message": data}