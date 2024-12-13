from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import PreviredIndicator, UserLogin
from app.backend.classes.payroll_indicator_class import PayrollIndicatorClass
from app.backend.classes.payroll_uf_indicator_class import PayrollUfIndicatorClass
from app.backend.classes.payroll_utm_uta_indicator_class import PayrollUtmUtaIndicatorClass
from app.backend.classes.payroll_taxable_income_cap_indicator_class import PayrollTaxableIncomeCapIndicatorClass
from app.backend.classes.payroll_minium_taxable_income_indicator_class import PayrollMiniumTaxableIncomeIndicatorClass
from app.backend.classes.payroll_voluntary_previtional_indicator_class import PayrollVoluntaryPrevitionalIndicatorClass
from app.backend.classes.payroll_umployment_insurance_indicator_class import PayrollUmploymentInsuranceIndicatorClass
from app.backend.classes.payroll_afp_quote_indicator_class import PayrollAfpQuoteIndicatorClass
from app.backend.classes.payroll_family_asignation_indicator_class import PayrollFamilyAsignationIndicatorClass
from app.backend.classes.payroll_heavy_duty_quote_indicator_class import PayrollHeavyDutyQuoteIndicatorClass
from app.backend.classes.payroll_ccaf_indicator_class import PayrollCcafIndicatorClass
from app.backend.classes.payroll_other_indicator_class import PayrollCcafIndicatorClass
from app.backend.classes.payroll_other_indicator_class import PayrollOtherIndicatorClass
from app.backend.auth.auth_user import get_current_active_user

previred_indicators = APIRouter(
    prefix="/previred_indicators",
    tags=["PreviredIndicators"]
)

@previred_indicators.post("/{period}")
def index(period:str, db: Session = Depends(get_db)):

    PayrollIndicatorClass(db).get_all(period)
    PayrollUfIndicatorClass(db).get_all(period)
    PayrollUtmUtaIndicatorClass(db).get_all(period)
    PayrollUtmUtaIndicatorClass(db).get_all(period)
    PayrollMiniumTaxableIncomeIndicatorClass(db).get_all(period)
    PayrollVoluntaryPrevitionalIndicatorClass(db).get_all(period)
    PayrollUmploymentInsuranceIndicatorClass(db).get_all(period)
    PayrollAfpQuoteIndicatorClass(db).get_all(period)
    PayrollFamilyAsignationIndicatorClass(db).get_all(period)
    PayrollHeavyDutyQuoteIndicatorClass(db).get_all(period)
    PayrollCcafIndicatorClass(db).get_all(period)
    PayrollOtherIndicatorClass(db).get_all(period)

    return {"message": 1}

@previred_indicators.post("/store")
def store(previred_indicator:PreviredIndicator, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    previred_indicator_inputs = previred_indicator.dict()

    PayrollIndicatorClass(db).store(previred_indicator_inputs)
    PayrollUfIndicatorClass(db).store(previred_indicator_inputs)
    PayrollUtmUtaIndicatorClass(db).store(previred_indicator_inputs)
    PayrollTaxableIncomeCapIndicatorClass(db).store(previred_indicator_inputs)
    PayrollMiniumTaxableIncomeIndicatorClass(db).store(previred_indicator_inputs)
    PayrollVoluntaryPrevitionalIndicatorClass(db).store(previred_indicator_inputs)
    PayrollUmploymentInsuranceIndicatorClass(db).store(previred_indicator_inputs)
    PayrollAfpQuoteIndicatorClass(db).store(previred_indicator_inputs)
    PayrollFamilyAsignationIndicatorClass(db).store(previred_indicator_inputs)
    PayrollHeavyDutyQuoteIndicatorClass(db).store(previred_indicator_inputs)
    PayrollCcafIndicatorClass(db).store(previred_indicator_inputs)
    PayrollOtherIndicatorClass(db).store(previred_indicator_inputs)

    return {"message": 1}