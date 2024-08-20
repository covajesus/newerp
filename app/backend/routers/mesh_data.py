from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import MeshDatum, UserLogin
from app.backend.classes.mesh_datum_class import MeshDataClass
from app.backend.auth.auth_user import get_current_active_user
from app.backend.classes.document_employee_class import DocumentEmployeeClass

mesh_data = APIRouter(
    prefix="/mesh_data",
    tags=["MeshData"]
)

@mesh_data.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = MeshDataClass(db).get_all()

    return {"message": data}

@mesh_data.post("/store")
def store(mesh_datum:MeshDatum, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    mesh_datum_inputs = mesh_datum.dict()
    document_id = DocumentEmployeeClass(db).store(mesh_datum_inputs)
    mesh_datum_inputs['document_employee_id'] = document_id
    data = MeshDataClass(db).store(mesh_datum_inputs)

    return {"message": data}

@mesh_data.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = MeshDataClass(db).delete(id)

    return {"message": data}