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
from app.backend.classes.payroll_month_indicator_class import PayrollMonthIndicatorClass
from app.backend.classes.helper_class import HelperClass
from app.backend.auth.auth_user import get_current_active_user

payroll_indicators = APIRouter(
    prefix="/payroll_indicators",
    tags=["Payroll_Indicators"]
)

@payroll_indicators.post("/store")
def store(provisional_indicator:ProvisionalIndicator, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    provisional_indicator_inputs = provisional_indicator.dict()

    period_indicator_existence = PayrollIndicatorClass(db).count(provisional_indicator_inputs['period'])

    if period_indicator_existence == 0:
        month_id = 1
        data_payroll_month_indicator = PayrollMonthIndicatorClass(db).store(month_id, provisional_indicator_inputs)
        provisional_indicator_inputs['indicator_id'] = data_payroll_month_indicator
        provisional_indicator_inputs['indicator_type_id'] = 16
        PayrollIndicatorClass(db).store(provisional_indicator_inputs)

        month_id = 2
        data_payroll_month_indicator = PayrollMonthIndicatorClass(db).store(month_id, provisional_indicator_inputs)
        provisional_indicator_inputs['indicator_id'] = data_payroll_month_indicator
        provisional_indicator_inputs['indicator_type_id'] = 16
        PayrollIndicatorClass(db).store(provisional_indicator_inputs)

        month_id = 3
        data_payroll_month_indicator = PayrollMonthIndicatorClass(db).store(month_id, provisional_indicator_inputs)
        provisional_indicator_inputs['indicator_id'] = data_payroll_month_indicator
        provisional_indicator_inputs['indicator_type_id'] = 16
        PayrollIndicatorClass(db).store(provisional_indicator_inputs)

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

@payroll_indicators.get("/scrape/{period}")
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
            
            data = [None] * 128  # Inicializa la lista con seis elementos None

            payroll_month_indicators = PayrollMonthIndicatorClass(db).get(1, period)

            data[3] = payroll_month_indicators.month_value

            payroll_month_indicators = PayrollMonthIndicatorClass(db).get(2, period)

            data[5] = payroll_month_indicators.month_value

            payroll_month_indicators = PayrollMonthIndicatorClass(db).get(3, period)

            data[10] = payroll_month_indicators.month_value
            
            uf_value_current_month = payroll_uf_indicators.uf_value_current_month
            data[4] = uf_value_current_month
            
            uf_value_last_month = payroll_uf_indicators.uf_value_last_month
            data[6] = uf_value_last_month
            
            payroll_utm_uta_indicators = PayrollUtmUtaIndicatorClass(db).get_all(period)

            utm_value_current_month = payroll_utm_uta_indicators.utm_value_current_month
            data[11] = utm_value_current_month
            
            uta_value_current_month = payroll_utm_uta_indicators.uta_value_current_month
            data[12] = uta_value_current_month

            payroll_taxable_income_cap_indicators = PayrollTaxableIncomeCapIndicatorClass(db).get(period)

            afp_value = payroll_taxable_income_cap_indicators.afp
            data[15] = afp_value
            
            ips_value = payroll_taxable_income_cap_indicators.ips
            data[17] = ips_value

            unemployment_value = payroll_taxable_income_cap_indicators.unemployment
            data[19] = unemployment_value

            payroll_minimun_income_indicators = PayrollMiniumTaxableIncomeIndicatorClass(db).get(period)

            dependent_independent_workers = payroll_minimun_income_indicators.dependent_independent_workers
            data[22] = dependent_independent_workers

            under_18_over_65 = payroll_minimun_income_indicators.under_18_over_65
            data[24] = under_18_over_65

            particular_home = payroll_minimun_income_indicators.particular_home
            data[26] = particular_home

            no_remunerations = payroll_minimun_income_indicators.no_remunerations
            data[28] = no_remunerations

            payroll_voluntary_previtional_indicators = PayrollVoluntaryPrevitionalIndicatorClass(db).get(period)

            voluntary_pension_savings_monthly = payroll_voluntary_previtional_indicators.voluntary_pension_savings_monthly
            data[31] = voluntary_pension_savings_monthly

            voluntary_pension_savings_annual = payroll_voluntary_previtional_indicators.voluntary_pension_savings_annual
            data[33] = voluntary_pension_savings_annual

            payroll_agreed_deposit_indicators = PayrollAgreedDepositIndicatorClass(db).get(period)

            agreed_deposit_value = payroll_agreed_deposit_indicators.agreed_deposit
            data[36] = agreed_deposit_value

            payroll_umployment_insurance_indicators = PayrollUmploymentInsuranceIndicatorClass(db).get(1, period)

            data[43] = payroll_umployment_insurance_indicators.employer
            data[44] = payroll_umployment_insurance_indicators.worker

            payroll_umployment_insurance_indicators = PayrollUmploymentInsuranceIndicatorClass(db).get(2, period)

            data[46] = payroll_umployment_insurance_indicators.employer
            data[47] = payroll_umployment_insurance_indicators.worker

            payroll_umployment_insurance_indicators = PayrollUmploymentInsuranceIndicatorClass(db).get(3, period)

            data[49] = payroll_umployment_insurance_indicators.employer
            data[50] = payroll_umployment_insurance_indicators.worker

            payroll_umployment_insurance_indicators = PayrollUmploymentInsuranceIndicatorClass(db).get(4, period)

            data[52] = payroll_umployment_insurance_indicators.employer
            data[53] = payroll_umployment_insurance_indicators.worker

            payroll_afp_quote_indicators = PayrollAfpQuoteIndicatorClass(db).get(1, period)

            data[63] = payroll_afp_quote_indicators.dependent_rate_afp
            data[64] = payroll_afp_quote_indicators.dependent_sis
            data[65] = payroll_afp_quote_indicators.independent_rate_afp

            payroll_afp_quote_indicators = PayrollAfpQuoteIndicatorClass(db).get(2, period)

            data[67] = payroll_afp_quote_indicators.dependent_rate_afp
            data[68] = payroll_afp_quote_indicators.dependent_sis
            data[69] = payroll_afp_quote_indicators.independent_rate_afp

            payroll_afp_quote_indicators = PayrollAfpQuoteIndicatorClass(db).get(3, period)

            data[71] = payroll_afp_quote_indicators.dependent_rate_afp
            data[72] = payroll_afp_quote_indicators.dependent_sis
            data[73] = payroll_afp_quote_indicators.independent_rate_afp

            payroll_afp_quote_indicators = PayrollAfpQuoteIndicatorClass(db).get(4, period)

            data[75] = payroll_afp_quote_indicators.dependent_rate_afp
            data[76] = payroll_afp_quote_indicators.dependent_sis
            data[77] = payroll_afp_quote_indicators.independent_rate_afp

            payroll_afp_quote_indicators = PayrollAfpQuoteIndicatorClass(db).get(5, period)

            data[79] = payroll_afp_quote_indicators.dependent_rate_afp
            data[80] = payroll_afp_quote_indicators.dependent_sis
            data[81] = payroll_afp_quote_indicators.independent_rate_afp

            payroll_afp_quote_indicators = PayrollAfpQuoteIndicatorClass(db).get(6, period)

            data[83] = payroll_afp_quote_indicators.dependent_rate_afp
            data[84] = payroll_afp_quote_indicators.dependent_sis
            data[85] = payroll_afp_quote_indicators.independent_rate_afp

            payroll_afp_quote_indicators = PayrollAfpQuoteIndicatorClass(db).get(7, period)

            data[87] = payroll_afp_quote_indicators.dependent_rate_afp
            data[88] = payroll_afp_quote_indicators.dependent_sis
            data[89] = payroll_afp_quote_indicators.independent_rate_afp

            payroll_family_asignation_indicators = PayrollFamilyAsignationIndicatorClass(db).get(1, period)

            data[95] = payroll_family_asignation_indicators.amount
            data[96] = payroll_family_asignation_indicators.minimum_value_rate
            data[97] = payroll_family_asignation_indicators.top_value_rate

            payroll_family_asignation_indicators = PayrollFamilyAsignationIndicatorClass(db).get(2, period)

            data[98] = payroll_family_asignation_indicators.amount
            data[99] = payroll_family_asignation_indicators.minimum_value_rate
            data[100] = payroll_family_asignation_indicators.top_value_rate

            payroll_family_asignation_indicators = PayrollFamilyAsignationIndicatorClass(db).get(3, period)

            data[101] = payroll_family_asignation_indicators.amount
            data[102] = payroll_family_asignation_indicators.minimum_value_rate
            data[103] = payroll_family_asignation_indicators.top_value_rate

            payroll_family_asignation_indicators = PayrollFamilyAsignationIndicatorClass(db).get(4, period)

            data[104] = payroll_family_asignation_indicators.amount
            data[105] = payroll_family_asignation_indicators.minimum_value_rate
            data[106] = payroll_family_asignation_indicators.top_value_rate

            payroll_heavy_duty_quote_indicators = PayrollHeavyDutyQuoteIndicatorClass(db).get(1, period)

            data[113] = payroll_heavy_duty_quote_indicators.job_position
            data[114] = payroll_heavy_duty_quote_indicators.employer
            data[115] = payroll_heavy_duty_quote_indicators.worker

            payroll_heavy_duty_quote_indicators = PayrollHeavyDutyQuoteIndicatorClass(db).get(2, period)

            data[117] = payroll_heavy_duty_quote_indicators.job_position
            data[118] = payroll_heavy_duty_quote_indicators.employer
            data[119] = payroll_heavy_duty_quote_indicators.worker

            payroll_ccaf_indicators = PayrollCcafIndicatorClass(db).get(period)

            data[122] = payroll_ccaf_indicators.ccaf
            data[124] = payroll_ccaf_indicators.fonasa

            payroll_other_indicators = PayrollOtherIndicatorClass(db).get(period, 1)

            data[125] = payroll_other_indicators.other_value

            payroll_other_indicators = PayrollOtherIndicatorClass(db).get(period, 2)

            data[126] = payroll_other_indicators.other_value

            payroll_other_indicators = PayrollOtherIndicatorClass(db).get(period, 3)

            data[127] = payroll_other_indicators.other_value

            return data
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": "Error en el servidor"}