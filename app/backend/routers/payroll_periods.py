from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin
from app.backend.classes.payroll_period_class import PayrollPeriodClass
from app.backend.auth.auth_user import get_current_active_user

payroll_periods = APIRouter(
    prefix="/payroll_periods",
    tags=["PayrollPeriods"]
)

@payroll_periods.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PayrollPeriodClass(db).get_all()

    return {"message": data}

@payroll_periods.get("/check")
def check(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PayrollPeriodClass(db).check()

    return {"message": data}