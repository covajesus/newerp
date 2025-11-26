from fastapi import APIRouter, Depends, Response, UploadFile, File
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import ProgressiveVacation, UploadProgressiveVacation, UserLogin
from app.backend.classes.progressive_vacation_class import ProgressiveVacationClass
from app.backend.classes.document_employee_class import DocumentEmployeeClass
from app.backend.classes.dropbox_class import DropboxClass
from app.backend.auth.auth_user import get_current_active_user
import os

progressive_vacations = APIRouter(
    prefix="/progressive_vacations",
    tags=["ProgressiveVacations"]
)

@progressive_vacations.get("/get_all_with_no_pagination/{rut}")
def get_all_with_no_pagination(rut: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ProgressiveVacationClass(db).get_all_with_no_pagination(rut)

    return {"message": data}

@progressive_vacations.get("/all/{rut}/{page}")
def index(rut: int, page: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ProgressiveVacationClass(db).get_all(rut, page)

    return {"message": data}

@progressive_vacations.get("/pdf_all/{rut}/{page}")
def pdf_index(rut: int, page: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ProgressiveVacationClass(db).pdf_get_all(rut, 1)

    return {"message": data}

@progressive_vacations.get("/total_vacation_days_in_company")
def total_vacation_days_in_company(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ProgressiveVacationClass(db).calculate_total_vacation_days()

    return {"message": data}

@progressive_vacations.post("/store")
def store(progressive_vacation:ProgressiveVacation, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    progressive_vacation_inputs = progressive_vacation.dict()

    document_id = DocumentEmployeeClass(db).store(progressive_vacation_inputs)
    progressive_vacation_inputs['document_employee_id'] = document_id
    data = ProgressiveVacationClass(db).store(progressive_vacation_inputs)

    return {"message": data}

@progressive_vacations.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    response_1 = ProgressiveVacationClass(db).delete(id)
    document_employee = DocumentEmployeeClass(db).get("id", id)
    response_2 = DocumentEmployeeClass(db).delete(id)

    if response_1 == 1 and response_2 == 1:
        if document_employee.support != '' and document_employee.support != None:
            response = DropboxClass(db).delete('/employee_documents/', document_employee.support)
        else:
            response = 1

        if response == 1:
            data = 1
        else:
            data = 0
    else:
        data = 0
    
    return {"message": data}

@progressive_vacations.get("/legal/{rut}")
def legal(rut: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ProgressiveVacationClass(db).legal(rut)

    return {"message": data}

@progressive_vacations.get("/taken/{rut}")
def taken(rut: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ProgressiveVacationClass(db).taken(rut)

    return {"message": data}

@progressive_vacations.get("/balance/{legal}/{taken}")
def balance(legal: int, taken: int, db: Session = Depends(get_db)):
    data = ProgressiveVacationClass(db).balance(legal, taken)

    return {"message": data}

@progressive_vacations.post("/upload")
def upload(form_data: UploadProgressiveVacation = Depends(UploadProgressiveVacation.as_form), support: UploadFile = File(...), session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    dropbox_client = DropboxClass(db)

    filename = dropbox_client.upload(name=form_data.rut, description='vacaciones_progresivas', data=support,
                                 dropbox_path='/employee_documents/', computer_path=os.path.join(os.path.dirname(__file__)))
    
    vacation = ProgressiveVacationClass(db).get("id", form_data.progressive_vacation_id)
    DocumentEmployeeClass(db).sign(vacation.document_employee_id)
    data = DocumentEmployeeClass(db).update_file(vacation.document_employee_id, filename)
    
    return {"message": data}

@progressive_vacations.get("/download/{id}")
def download(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ProgressiveVacationClass(db).download(id)

    return {"message": data}

@progressive_vacations.get("/sign/{id}")
def sign(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = DocumentEmployeeClass(db).sign(id)

    return {"message": data}