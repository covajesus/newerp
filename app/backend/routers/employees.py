from fastapi import APIRouter, Depends, Request, Response, UploadFile, File
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Employee, UpdateEmployee, SearchEmployee, UserLogin, EmployeeList, UploadSignature, UploadPicture
from app.backend.classes.employee_class import EmployeeClass
from app.backend.auth.auth_user import get_current_active_user
import base64
import os
from app.backend.classes.dropbox_class import DropboxClass

employees = APIRouter(
    prefix="/employees",
    tags=["Employees"]
)

@employees.post("/")
def index(employee: EmployeeList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EmployeeClass(db).get_all(employee.rut, employee.rol_id, employee.page)

    return {"message": data}

@employees.post("/search")
def search(search_data: SearchEmployee, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    search_data = search_data.dict()

    employees = EmployeeClass(db).search(search_data, search_data['page'])

    return {"message": employees}

@employees.post("/signature")
def signature(form_data: UploadSignature = Depends(UploadSignature.as_form), session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    dropbox_client = DropboxClass(db)

    filename = dropbox_client.sign(name=form_data.rut, description='firma', data=form_data.signature,
                                 dropbox_path='/signatures/', computer_path=os.path.join(os.path.dirname(__file__)))
    
    employee_inputs = {}

    employee_inputs['signature'] = filename

    employee_inputs['signature_type_id'] = form_data.signature_type_id

    EmployeeClass(db).update(form_data.rut, employee_inputs)
    
    return {"message": form_data.signature}

@employees.get("/get_birthdays")
def get_birthdays(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EmployeeClass(db).get_birthdays()

    return {"message": data}

@employees.get("/get_genders_total")
def gender_totals(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EmployeeClass(db).gender_totals()

    return {"message": data}

@employees.post("/store")
def store(employee:Employee, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    employee_inputs = employee.dict()
    data = EmployeeClass(db).store(employee_inputs)

    return {"message": data}

@employees.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EmployeeClass(db).get("rut", id)

    return {"message": data}

@employees.get("/validate_rut/{rut}")
def validate_rut(rut:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EmployeeClass(db).validate_rut(rut)

    return {"message": data}

@employees.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EmployeeClass(db).delete(id)

    return {"message": data}

@employees.delete("/delete/signature/{rut}")
def delete(rut:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    employee_inputs = {}  # Inicializa el diccionario
        
    employee_inputs['signature'] = ''

    employee_inputs['signature_type_id'] = 0

    EmployeeClass(db).update(rut, employee_inputs)

    return {"message": rut}

@employees.patch("/update/{id}")
def update(id: int, employee: UpdateEmployee, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    employee_inputs = employee.dict()
    
    data = EmployeeClass(db).update(id, employee_inputs)

    return {"message": data}

@employees.get("/validate_cellphone/{cellphone}")
def validate(cellphone: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EmployeeClass(db).validate_cellphone(cellphone)

    return {"message": data}

@employees.post("/upload/picture")
def upload(form_data: UploadPicture = Depends(UploadPicture.as_form), picture: UploadFile = File(...), session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    dropbox_client = DropboxClass(db)

    filename = dropbox_client.upload(name=form_data.rut, description='foto', data=picture,
                                 dropbox_path='/pictures/', computer_path=os.path.join(os.path.dirname(__file__)))
    
    employee_inputs = {}

    employee_inputs['picture'] = filename

    data = EmployeeClass(db).update(form_data.rut, employee_inputs)

    return {"message": data}

@employees.delete("/delete/picture/{rut}")
def delete(rut:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    employee = EmployeeClass(db).one_simple_get(rut)

    employee_inputs = {}  # Inicializa el diccionario
        
    employee_inputs['picture'] = ''

    EmployeeClass(db).update(rut, employee_inputs)

    dropbox_client = DropboxClass(db)

    dropbox_client.delete('/pictures/', employee.picture)

    return {"message": rut}

@employees.get("/select_inputs")
def select_inputs(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    employees = EmployeeClass(db).get_all_with_no_paginator()

    return {"message": employees}

@employees.get("/full_details")
def full_details(db: Session = Depends(get_db)):
    employees = EmployeeClass(db).full_details()

    return {"message": employees}