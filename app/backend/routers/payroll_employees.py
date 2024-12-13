from fastapi import APIRouter, Depends, Form
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin, SearchPayrollEmployee
from app.backend.classes.payroll_employee_class import PayrollEmployeeClass
from app.backend.auth.auth_user import get_current_active_user

payroll_employees = APIRouter(
    prefix="/payroll_employees",
    tags=["PayrollEmployees"]
)

@payroll_employees.get("/{period}")
def index(period: str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PayrollEmployeeClass(db).get_all(period)

    return {"message": data}

@payroll_employees.get("/detail/{rut}/{period}")
def detail(rut:int, period: str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PayrollEmployeeClass(db).get(rut, period)

    return {"message": data}

@payroll_employees.post("/search")
def search(search_data: SearchPayrollEmployee, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    search_data = search_data.dict()

    payroll_employees = PayrollEmployeeClass(db).search(search_data)

    return {"message": payroll_employees}