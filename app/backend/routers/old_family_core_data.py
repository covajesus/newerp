from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin
from app.backend.classes.old_family_core_datum_class import OldFamilyCoreDatumClass
from app.backend.classes.family_core_datum_class import FamilyCoreDatumClass
from app.backend.auth.auth_user import get_current_active_user
import json

old_family_core_data = APIRouter(
    prefix="/old_family_core_data",
    tags=["OldFamilyCoreDatum"]
)

@old_family_core_data.post("/transfer/{rut}/{end_document_type_id}")
def transfer(rut: int, end_document_type_id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    family_data = FamilyCoreDatumClass(db).get('employee_rut', rut, 2)
    family_data = json.loads(family_data)

    for family_datum in family_data:
        old_family_inputs = {
            'family_type_id': family_datum['family_type_id'],
            'employee_rut': family_datum['employee_rut'],
            'gender_id': family_datum['gender_id'],
            'rut': family_datum['rut'],
            'names': family_datum['names'],
            'father_lastname': family_datum['father_lastname'],
            'mother_lastname': family_datum['mother_lastname'],
            'born_date': family_datum['born_date'],
            'support': family_datum['support'],
        }

        OldFamilyCoreDatumClass(db).store(old_family_inputs)
        if end_document_type_id == 1:
            FamilyCoreDatumClass(db).delete(family_datum.id)

    return {"message": f"Datos del núcleo familiar transferidos para el RUT {rut}"}

@old_family_core_data.get("/edit/{rut}/{get_type_id}")
def edit(rut:int, get_type_id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):

    data = OldFamilyCoreDatumClass(db).get("employee_rut", rut, get_type_id)

    return {"message": data}
