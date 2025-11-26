from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin
from app.backend.classes.payroll_calculation_class import PayrollCalculationClass
from app.backend.classes.payroll_calculated_employee_class import PayrollCalculatedEmployeeClass
from app.backend.auth.auth_user import get_current_active_user

payroll_calculations = APIRouter(
    prefix="/payroll_calculations",
    tags=["PayrollCalculations"]
)

@payroll_calculations.get("/{rut}/{period}")
def calculate(rut:int, period:str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PayrollCalculationClass(db).calculate(rut, period)

    return {"message": data}

@payroll_calculations.get("/check/{period}")
def calculate(period:str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PayrollCalculatedEmployeeClass(db).check(period)

    return {"message": data}