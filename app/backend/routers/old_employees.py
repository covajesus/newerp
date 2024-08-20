from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import OldEmployee, UserLogin
from app.backend.classes.old_employee_class import OldEmployeeClass
from app.backend.classes.employee_class import EmployeeClass
from app.backend.auth.auth_user import get_current_active_user

old_employees = APIRouter(
    prefix="/old_employees",
    tags=["OldEmployees"]
)

@old_employees.post("/transfer")
def transfer(old_employee: OldEmployee, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    old_employee_inputs = old_employee.dict()

    data = OldEmployeeClass(db).store(old_employee_inputs)

    if old_employee_inputs['end_document_type_id'] == 1:
        EmployeeClass(db).delete(old_employee_inputs["rut"])

    return {"message": data}

@old_employees.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = OldEmployeeClass(db).get("rut", id)

    return {"message": data}

