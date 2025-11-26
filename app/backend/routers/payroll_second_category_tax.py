from fastapi import APIRouter, Depends, Form
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin, PayrollSecondCategoryTax
from app.backend.classes.payroll_second_category_taxes_class import PayrollSecondCategoryTaxClass
from app.backend.classes.payroll_indicator_class import PayrollIndicatorClass
from app.backend.auth.auth_user import get_current_active_user

payroll_second_category_taxes = APIRouter(
    prefix="/payroll_second_category_taxes",
    tags=["PayrollSecondCategoryTax"]
)

@payroll_second_category_taxes.post("/store")
def store(payroll_inputs: PayrollSecondCategoryTax = Depends(PayrollSecondCategoryTax.as_form), session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    payroll_inputs = payroll_inputs.dict()

    period_indicator_existence = PayrollIndicatorClass(db).count(payroll_inputs['period'])

    if period_indicator_existence == 0:
        
        data = PayrollSecondCategoryTaxClass(db).store(payroll_inputs)

        return {"message": data}