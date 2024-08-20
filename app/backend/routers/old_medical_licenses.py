from fastapi import APIRouter, Depends, File, UploadFile
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin
from app.backend.classes.medical_license_class import MedicalLicenseClass
from app.backend.auth.auth_user import get_current_active_user
from app.backend.db.models import MedicalLicenseModel
from app.backend.classes.old_medical_license_class import OldMedicalLicenseClass
from sqlalchemy import delete

import os

old_medical_licenses = APIRouter(
    prefix="/old_medical_licenses",
    tags=["OldMedicalLicenses"]
)

@old_medical_licenses.post("/transfer/{rut}/{end_document_type_id}")
def transfer(rut: int, end_document_type_id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    medical_licenses = db.query(MedicalLicenseModel).filter(MedicalLicenseModel.rut == rut).all()

    for medical_license in medical_licenses:
        old_medical_license_inputs = {
            'document_employee_id': medical_license.document_employee_id,
            'medical_license_type_id': medical_license.medical_license_type_id,
            'patology_type_id': medical_license.patology_type_id,
            'period': medical_license.period,
            'rut': medical_license.rut,
            'folio': medical_license.folio,
            'since': medical_license.since,
            'until': medical_license.until,
            'days': medical_license.days,
        }

        OldMedicalLicenseClass(db).store(old_medical_license_inputs)
        if end_document_type_id == 1:
            MedicalLicenseClass(db).delete(medical_license.id)

    return {"message": f"Datos de licencias médicas transferidos para el RUT {rut}"}

@old_medical_licenses.get("/edit/{rut}/{page}")
def edit(rut:int, page:int = None, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = OldMedicalLicenseClass(db).get("rut", rut, 2, page)
    
    return {"message": data}