from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.db.models import UniformTypeModel
from app.backend.schemas import UniformType, UpdateUniformType, UserLogin
from app.backend.auth.auth_user import get_current_active_user

uniform_types = APIRouter(
    prefix="/uniform_types",
    tags=["Uniform_Types"]
)

@uniform_types.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = db.query(UniformTypeModel).all()

    return {"message": data}

@uniform_types.post("/store")
def store(uniform_type:UniformType, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    uniform_type_inputs = uniform_type.dict()
    data = UniformTypeModel(**uniform_type_inputs)

    db.add(data)
    db.commit()

    return {"message": data}

@uniform_types.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = db.query(UniformTypeModel).filter(UniformTypeModel.id == id).first()

    return {"message": data}

@uniform_types.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = db.query(UniformTypeModel).filter(UniformTypeModel.id == id)

    if not data.first():
        return {"message": "Uniforme no encontrado!"}
    
    data.delete(synchronize_session=False)

    db.commit()

    return {"message": "Uniforme eliminado!"}

@uniform_types.patch("/update/{id}")
def update(id:int, uniform_type:UpdateUniformType, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    existing_uniform_type = db.query(UniformTypeModel).filter(UniformTypeModel.id == id).one_or_none()

    if not existing_uniform_type:
        return {"message": "Uniforme no encontrado!"}

    existing_uniform_type_data = uniform_type.dict(exclude_unset=True)
    for key, value in existing_uniform_type_data.items():
        setattr(existing_uniform_type, key, value)

    db.commit()

    return {"message": "Uniforme actualizado", "data": existing_uniform_type}