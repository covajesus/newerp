from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import OldDocumentEmployee, UserLogin
from app.backend.classes.old_document_employee_class import OldDocumentEmployeeClass
from app.backend.classes.document_employee_class import DocumentEmployeeClass
from app.backend.classes.dropbox_class import DropboxClass
import os
from app.backend.auth.auth_user import get_current_active_user
from app.backend.db.models import DocumentEmployeeModel, OldDocumentEmployeeModel
from sqlalchemy import delete

old_documents_employees = APIRouter(
    prefix="/old_documents_employees",
    tags=["OldDocumentsEmployees"]
)

@old_documents_employees.post("/transfer/{rut}/{end_document_type_id}")
def transfer(rut: int, end_document_type_id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    document_data = db.query(DocumentEmployeeModel).filter(DocumentEmployeeModel.rut == rut).all()

    for docucment_datum in document_data:
        old_document_datum_inputs = {
            'status_id': docucment_datum.status_id,
            'document_type_id': docucment_datum.document_type_id,
            'rut': docucment_datum.rut,
            'support': docucment_datum.support,
        }

        OldDocumentEmployeeClass(db).store(old_document_datum_inputs)
        if end_document_type_id == 1:
            DocumentEmployeeClass(db).delete(docucment_datum.id)

    return {"message": f"Documentos transferidos para el RUT {rut}"}

@old_documents_employees.get("/edit/{rut}")
def edit(rut:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = OldDocumentEmployeeClass(db).get("rut", rut)

    return {"message": data}
