from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin
from app.backend.classes.payroll_umployment_insurance_indicator_class import PayrollUmploymentInsuranceIndicatorClass
from app.backend.auth.auth_user import get_current_active_user

payroll_umployment_insurances = APIRouter(
    prefix="/payroll_umployment_insurances",
    tags=["PayrollUmploymentInsurances"]
)

@payroll_umployment_insurances.get("/{contract_type_id}/{period}")
def index(contract_type_id:int, period:str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PayrollUmploymentInsuranceIndicatorClass(db).get(contract_type_id, period)

    return {"message": data}