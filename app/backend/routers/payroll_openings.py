# Dentro de la función scrape() en tu servidor FastAPI


from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import OpenPeriodPayroll, UserLogin, ClosePeriodPayroll
from app.backend.classes.payroll_class import PayrollClass
from app.backend.auth.auth_user import get_current_active_user

payroll_openings = APIRouter(
    prefix="/payroll_openings",
    tags=["PayrollOpenings"]
)

@payroll_openings.post("/open")
def open(open_period_payroll_inputs:OpenPeriodPayroll, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    open_period_payroll_inputs = open_period_payroll_inputs.dict()

    data = PayrollClass(db).open(open_period_payroll_inputs)

    return {"message": data}

@payroll_openings.post("/close")
def open(close_period_payroll_inputs:ClosePeriodPayroll, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    close_period_payroll_inputs = close_period_payroll_inputs.dict()

    data = PayrollClass(db).open(close_period_payroll_inputs)

    return {"message": data}