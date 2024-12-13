# Dentro de la función scrape() en tu servidor FastAPI


from fastapi import APIRouter, Depends
import httpx
from bs4 import BeautifulSoup
import requests
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import ProvisionalIndicator, UserLogin
from app.backend.classes.payroll_indicator_class import PayrollIndicatorClass
from app.backend.classes.payroll_uf_indicator_class import PayrollUfIndicatorClass
from app.backend.classes.payroll_utm_uta_indicator_class import PayrollUtmUtaIndicatorClass
from app.backend.classes.payroll_taxable_income_cap_indicator_class import PayrollTaxableIncomeCapIndicatorClass
from app.backend.classes.payroll_minium_taxable_income_indicator_class import PayrollMiniumTaxableIncomeIndicatorClass
from app.backend.classes.payroll_voluntary_previtional_indicator_class import PayrollVoluntaryPrevitionalIndicatorClass
from app.backend.classes.payroll_agreed_deposit_indicator_class import PayrollAgreedDepositIndicatorClass
from app.backend.classes.payroll_umployment_insurance_indicator_class import PayrollUmploymentInsuranceIndicatorClass
from app.backend.classes.payroll_afp_quote_indicator_class import PayrollAfpQuoteIndicatorClass
from app.backend.classes.payroll_family_asignation_indicator_class import PayrollFamilyAsignationIndicatorClass
from app.backend.classes.payroll_heavy_duty_quote_indicator_class import PayrollHeavyDutyQuoteIndicatorClass
from app.backend.classes.payroll_ccaf_indicator_class import PayrollCcafIndicatorClass
from app.backend.classes.payroll_other_indicator_class import PayrollOtherIndicatorClass
from app.backend.classes.helper_class import HelperClass
from app.backend.auth.auth_user import get_current_active_user

provisional_indicators = APIRouter(
    prefix="/provisional_indicators",
    tags=["Provisional_Indicators"]
)

@provisional_indicators.post("/store")
def store(provisional_indicator:ProvisionalIndicator, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    provisional_indicator_inputs = provisional_indicator.dict()

    data_payroll_uf_indicator = PayrollUfIndicatorClass(db).store(provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_payroll_uf_indicator
    provisional_indicator_inputs['indicator_type_id'] = 1
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    data_payroll_utm_uta_indicator = PayrollUtmUtaIndicatorClass(db).store(provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_payroll_utm_uta_indicator
    provisional_indicator_inputs['indicator_type_id'] = 2
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    data_taxable_income_cap_indicator = PayrollTaxableIncomeCapIndicatorClass(db).store(provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_taxable_income_cap_indicator
    provisional_indicator_inputs['indicator_type_id'] = 3
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    data_minium_taxable_income_indicator = PayrollMiniumTaxableIncomeIndicatorClass(db).store(provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_minium_taxable_income_indicator
    provisional_indicator_inputs['indicator_type_id'] = 4
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    data_voluntary_previtional_indicator = PayrollVoluntaryPrevitionalIndicatorClass(db).store(provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_voluntary_previtional_indicator
    provisional_indicator_inputs['indicator_type_id'] = 5
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    data_agreed_deposit_indicator = PayrollAgreedDepositIndicatorClass(db).store(provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_agreed_deposit_indicator
    provisional_indicator_inputs['indicator_type_id'] = 6
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    contract_type_id = 1
    data_umployment_insurance_indicator = PayrollUmploymentInsuranceIndicatorClass(db).store(contract_type_id, provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_umployment_insurance_indicator
    provisional_indicator_inputs['indicator_type_id'] = 7
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    contract_type_id = 2
    data_umployment_insurance_indicator = PayrollUmploymentInsuranceIndicatorClass(db).store(contract_type_id, provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_umployment_insurance_indicator
    provisional_indicator_inputs['indicator_type_id'] = 7
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    contract_type_id = 3
    data_umployment_insurance_indicator = PayrollUmploymentInsuranceIndicatorClass(db).store(contract_type_id, provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_umployment_insurance_indicator
    provisional_indicator_inputs['indicator_type_id'] = 7
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    contract_type_id = 4
    data_umployment_insurance_indicator = PayrollUmploymentInsuranceIndicatorClass(db).store(contract_type_id, provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_umployment_insurance_indicator
    provisional_indicator_inputs['indicator_type_id'] = 7
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    pention_id = 1
    data_afp_quote_indicator = PayrollAfpQuoteIndicatorClass(db).store(pention_id, provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_afp_quote_indicator
    provisional_indicator_inputs['indicator_type_id'] = 8
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    pention_id = 2
    data_afp_quote_indicator = PayrollAfpQuoteIndicatorClass(db).store(pention_id, provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_afp_quote_indicator
    provisional_indicator_inputs['indicator_type_id'] = 8
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    pention_id = 3
    data_afp_quote_indicator = PayrollAfpQuoteIndicatorClass(db).store(pention_id, provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_afp_quote_indicator
    provisional_indicator_inputs['indicator_type_id'] = 8
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    pention_id = 4
    data_afp_quote_indicator = PayrollAfpQuoteIndicatorClass(db).store(pention_id, provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_afp_quote_indicator
    provisional_indicator_inputs['indicator_type_id'] = 8
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    pention_id = 5
    data_afp_quote_indicator = PayrollAfpQuoteIndicatorClass(db).store(pention_id, provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_afp_quote_indicator
    provisional_indicator_inputs['indicator_type_id'] = 8
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    pention_id = 6
    data_afp_quote_indicator = PayrollAfpQuoteIndicatorClass(db).store(pention_id, provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_afp_quote_indicator
    provisional_indicator_inputs['indicator_type_id'] = 8
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    pention_id = 7
    data_afp_quote_indicator = PayrollAfpQuoteIndicatorClass(db).store(pention_id, provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_afp_quote_indicator
    provisional_indicator_inputs['indicator_type_id'] = 8
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    section_id = 1
    data_family_asignation_indicator = PayrollFamilyAsignationIndicatorClass(db).store(section_id, provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_family_asignation_indicator
    provisional_indicator_inputs['indicator_type_id'] = 9
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    section_id = 2
    data_family_asignation_indicator = PayrollFamilyAsignationIndicatorClass(db).store(section_id, provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_family_asignation_indicator
    provisional_indicator_inputs['indicator_type_id'] = 9
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    section_id = 3
    data_family_asignation_indicator = PayrollFamilyAsignationIndicatorClass(db).store(section_id, provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_family_asignation_indicator
    provisional_indicator_inputs['indicator_type_id'] = 9
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    section_id = 4
    data_family_asignation_indicator = PayrollFamilyAsignationIndicatorClass(db).store(section_id, provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_family_asignation_indicator
    provisional_indicator_inputs['indicator_type_id'] = 9
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    duty_type_id = 1
    data_heavy_duty_quote_indicator = PayrollHeavyDutyQuoteIndicatorClass(db).store(duty_type_id, provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_heavy_duty_quote_indicator
    provisional_indicator_inputs['indicator_type_id'] = 10
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    duty_type_id = 2
    data_heavy_duty_quote_indicator = PayrollHeavyDutyQuoteIndicatorClass(db).store(duty_type_id, provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = data_heavy_duty_quote_indicator
    provisional_indicator_inputs['indicator_type_id'] = 10
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    distribution_7_percent_health_indicator = PayrollCcafIndicatorClass(db).store(provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = distribution_7_percent_health_indicator
    provisional_indicator_inputs['indicator_type_id'] = 11
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    ccaf_indicator = PayrollCcafIndicatorClass(db).store(provisional_indicator_inputs)
    provisional_indicator_inputs['indicator_id'] = ccaf_indicator
    provisional_indicator_inputs['indicator_type_id'] = 12
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)
 
    other_type_id = 1
    other_indicator_mutual = PayrollOtherIndicatorClass(db).store(provisional_indicator_inputs, other_type_id)
    provisional_indicator_inputs['indicator_id'] = other_indicator_mutual
    provisional_indicator_inputs['indicator_type_id'] = 13
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    other_type_id = 2
    other_indicator_honorary = PayrollOtherIndicatorClass(db).store(provisional_indicator_inputs, other_type_id)
    provisional_indicator_inputs['indicator_id'] = other_indicator_honorary
    provisional_indicator_inputs['indicator_type_id'] = 14
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    other_type_id = 3
    other_indicator_gratification = PayrollOtherIndicatorClass(db).store(provisional_indicator_inputs, other_type_id)
    provisional_indicator_inputs['indicator_id'] = other_indicator_gratification
    provisional_indicator_inputs['indicator_type_id'] = 15
    PayrollIndicatorClass(db).store(provisional_indicator_inputs)

    return {"message": 1}

@provisional_indicators.get("/scrape/{period}")
async def scrape(period:str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        period_indicator_existence = PayrollIndicatorClass(db).count(period)

        if period_indicator_existence == 0:
            url = 'https://www.previred.com/indicadores-previsionales/'

            response = requests.get(url)

            soup = BeautifulSoup(response.text, 'html.parser')

            td_elements = soup.find_all('td')

            # Crea una lista vacía para almacenar los datos
            data = []

            for td in td_elements:
                datum = HelperClass().remove_from_string("$", td.text)
                datum = HelperClass().remove_from_string("RI", datum)
                datum = HelperClass().remove_from_string("R.I.", datum)
                datum = HelperClass().remove_from_string("%", datum)
                datum = HelperClass().replace("–", "0", datum)

                data.append(datum)

            period_title = data[0]

            period_title = HelperClass().split(" ", period_title)

            data[1] = 0

            return data
        else:
            payroll_uf_indicators = PayrollUfIndicatorClass(db).get_all(period)
            
            data = [None] * 125  # Inicializa la lista con seis elementos None
            
            uf_value_current_month = payroll_uf_indicators.uf_value_current_month
            data[4] = uf_value_current_month
            
            uf_value_last_month = payroll_uf_indicators.uf_value_last_month
            data[6] = uf_value_last_month
            
            return data
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": "Error en el servidor"}