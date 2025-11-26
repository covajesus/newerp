from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import MedicalLicenseType, UpdateMedicalLicenseType, UserLogin
from app.backend.classes.medical_license_type_class import MedicalLicenseTypeClass
from app.backend.auth.auth_user import get_current_active_user

medical_license_types = APIRouter(
    prefix="/medical_license_types",
    tags=["MedicalLicenseTypes"]
)

@medical_license_types.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = MedicalLicenseTypeClass(db).get_all()

    return {"message": data}

@medical_license_types.post("/store")
def store(medical_license_type:MedicalLicenseType, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    medical_license_type_inputs = medical_license_type.dict()
    data = MedicalLicenseTypeClass(db).store(medical_license_type_inputs)

    return {"message": data}

@medical_license_types.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = MedicalLicenseTypeClass(db).get("id", id)

    return {"message": data}

@medical_license_types.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = MedicalLicenseTypeClass(db).delete(id)

    return {"message": data}

@medical_license_types.patch("/update/{id}")
def update(id: int, medical_license_type: UpdateMedicalLicenseType, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = MedicalLicenseTypeClass(db).update(id, medical_license_type)

    return {"message": data}