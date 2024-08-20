from app.backend.db.models import PayrollVoluntaryPrevitionalIndicatorModel
from app.backend.classes.helper_class import HelperClass
from datetime import datetime

class PayrollVoluntaryPrevitionalIndicatorClass:
    def __init__(self, db):
        self.db = db

    def get(self, period):
        data = self.db.query(PayrollVoluntaryPrevitionalIndicatorModel).filter(PayrollVoluntaryPrevitionalIndicatorModel.period == period).first()

        return data
    
    def store(self, payroll_indicator_inputs):
        try:
            voluntary_pension_savings_monthly = HelperClass().remove_from_string(".", payroll_indicator_inputs['voluntary_pension_savings_monthly'])
            voluntary_pension_savings_monthly = HelperClass().replace(",", ".", voluntary_pension_savings_monthly)
            voluntary_pension_savings_annual = HelperClass().remove_from_string(".", payroll_indicator_inputs['voluntary_pension_savings_annual'])
            voluntary_pension_savings_annual = HelperClass().replace(",", ".", voluntary_pension_savings_annual)
        
            payroll_voluntary_previtional_indicator = PayrollVoluntaryPrevitionalIndicatorModel()
            payroll_voluntary_previtional_indicator.voluntary_pension_savings_monthly = voluntary_pension_savings_monthly
            payroll_voluntary_previtional_indicator.voluntary_pension_savings_annual = voluntary_pension_savings_annual
            payroll_voluntary_previtional_indicator.period = payroll_indicator_inputs['period']
            payroll_voluntary_previtional_indicator.added_date = datetime.now()
            self.db.add(payroll_voluntary_previtional_indicator)
            self.db.commit()
            
            inserted_id = payroll_voluntary_previtional_indicator.id

            return inserted_id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"