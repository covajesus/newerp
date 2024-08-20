from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.employee_contract_class import EmployeeContractClass
from app.backend.auth.auth_user import get_current_active_user
from app.backend.schemas import UserLogin
from app.backend.classes.vacation_class import VacationClass
from app.backend.classes.document_employee_class import DocumentEmployeeClass
from app.backend.classes.dropbox_class import DropboxClass
from app.backend.schemas import UploadEmployeeContract
from fastapi import File, UploadFile
import os

employee_contracts = APIRouter(
    prefix="/employee_contracts",
    tags=["EmployeeContracts"]
)

@employee_contracts.get("/edit/{rut}")
def index(rut:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EmployeeContractClass(db).get_all(rut)

    return {"message": data}

@employee_contracts.post("/upload")
def upload(form_data: UploadEmployeeContract = Depends(UploadEmployeeContract.as_form), support: UploadFile = File(...), session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    dropbox_client = DropboxClass(db)

    filename = dropbox_client.upload(name=form_data.rut, description='contrato_empleado', data=support,
                                 dropbox_path='/employee_contracts/', computer_path=os.path.join(os.path.dirname(__file__)))
    
    data = DocumentEmployeeClass(db).update_file(form_data.id, filename)

    return {"message": data}

@employee_contracts.get("/download/{id}")
def download(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EmployeeContractClass(db).download(id)

    return {"message": data}

@employee_contracts.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    document_employee = DocumentEmployeeClass(db).get("id", id)

    response = DocumentEmployeeClass(db).delete(id)

    if response == 1:
        if document_employee.support != None:
            response = DropboxClass(db).delete('/employee_contracts/', document_employee.support)

        if response == 1:
            data = 1
        else:
            data = response
    else:
        data = 0
    
    return {"message": data}