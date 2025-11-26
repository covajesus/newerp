from app.backend.db.models import PayrollUmploymentInsuranceIndicatorModel, PayrollIndicatorModel
from app.backend.classes.helper_class import HelperClass
from datetime import datetime

class PayrollUmploymentInsuranceIndicatorClass:
    def __init__(self, db):
        self.db = db

    def get(self, contract_type_id, period):
        data = self.db.query(PayrollUmploymentInsuranceIndicatorModel).filter(PayrollUmploymentInsuranceIndicatorModel.contract_type_id == contract_type_id, PayrollUmploymentInsuranceIndicatorModel.period == period).first()
        
        return data
    
    def store(self, contract_type_id, payroll_indicator_inputs):
        try:

            if contract_type_id == 1:
                indefinite_term_worker = HelperClass().remove_from_string(".", payroll_indicator_inputs['indefinite_term_worker'])
                indefinite_term_worker = HelperClass().replace(",", ".", indefinite_term_worker)
                indefinite_term_employeer = HelperClass().remove_from_string(".", payroll_indicator_inputs['indefinite_term_employeer'])
                indefinite_term_employeer = HelperClass().replace(",", ".", indefinite_term_employeer)

                payroll_umployment_insurance_indicator = PayrollUmploymentInsuranceIndicatorModel()
                payroll_umployment_insurance_indicator.contract_type_id = contract_type_id
                payroll_umployment_insurance_indicator.worker = indefinite_term_worker
                payroll_umployment_insurance_indicator.employer = indefinite_term_employeer
                payroll_umployment_insurance_indicator.period = payroll_indicator_inputs['period']
                payroll_umployment_insurance_indicator.added_date = datetime.now()
                self.db.add(payroll_umployment_insurance_indicator)
                self.db.commit()

            if contract_type_id == 2:
                fixed_term_worker = HelperClass().remove_from_string(".", payroll_indicator_inputs['fixed_term_worker'])
                fixed_term_worker = HelperClass().replace(",", ".", fixed_term_worker)
                fixed_term_employeer = HelperClass().remove_from_string(".", payroll_indicator_inputs['fixed_term_employeer'])
                fixed_term_employeer = HelperClass().replace(",", ".", fixed_term_employeer)

                payroll_umployment_insurance_indicator = PayrollUmploymentInsuranceIndicatorModel()
                payroll_umployment_insurance_indicator.contract_type_id = contract_type_id
                payroll_umployment_insurance_indicator.worker = fixed_term_worker
                payroll_umployment_insurance_indicator.employer = fixed_term_employeer
                payroll_umployment_insurance_indicator.period = payroll_indicator_inputs['period']
                payroll_umployment_insurance_indicator.added_date = datetime.now()
                self.db.add(payroll_umployment_insurance_indicator)
                self.db.commit()

            if contract_type_id == 3:
                indefinite_term_worker_11_years = HelperClass().remove_from_string(".", payroll_indicator_inputs['indefinite_term_worker_11_years'])
                indefinite_term_worker_11_years = HelperClass().replace(",", ".", indefinite_term_worker_11_years)
                indefinite_term_employeer_11_years = HelperClass().remove_from_string(".", payroll_indicator_inputs['indefinite_term_employeer_11_years'])
                indefinite_term_employeer_11_years = HelperClass().replace(",", ".", indefinite_term_employeer_11_years)

                payroll_umployment_insurance_indicator = PayrollUmploymentInsuranceIndicatorModel()
                payroll_umployment_insurance_indicator.contract_type_id = contract_type_id
                payroll_umployment_insurance_indicator.worker = indefinite_term_worker_11_years
                payroll_umployment_insurance_indicator.employer = indefinite_term_employeer_11_years
                payroll_umployment_insurance_indicator.period = payroll_indicator_inputs['period']
                payroll_umployment_insurance_indicator.added_date = datetime.now()
                self.db.add(payroll_umployment_insurance_indicator)
                self.db.commit()

            if contract_type_id == 4:
                domestic_worker = HelperClass().remove_from_string(".", payroll_indicator_inputs['domestic_worker'])
                domestic_worker = HelperClass().replace(",", ".", domestic_worker)
                domestic_employeer = HelperClass().remove_from_string(".", payroll_indicator_inputs['domestic_employeer'])
                domestic_employeer = HelperClass().replace(",", ".", domestic_employeer)

                payroll_umployment_insurance_indicator = PayrollUmploymentInsuranceIndicatorModel()
                payroll_umployment_insurance_indicator.contract_type_id = contract_type_id
                payroll_umployment_insurance_indicator.worker = domestic_worker
                payroll_umployment_insurance_indicator.employer = domestic_employeer
                payroll_umployment_insurance_indicator.period = payroll_indicator_inputs['period']
                payroll_umployment_insurance_indicator.added_date = datetime.now()
                self.db.add(payroll_umployment_insurance_indicator)
                self.db.commit()

            inserted_id = payroll_umployment_insurance_indicator.id

            return inserted_id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"