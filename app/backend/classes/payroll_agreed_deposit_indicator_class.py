from app.backend.classes.helper_class import HelperClass
from app.backend.db.models import PayrollAgreedDepositIndicatorModel
from datetime import datetime

class PayrollAgreedDepositIndicatorClass:
    def __init__(self, db):
        self.db = db

    def get(self, period):
        data = self.db.query(PayrollAgreedDepositIndicatorModel).filter(PayrollAgreedDepositIndicatorModel.period == period).first()

        return data
    
    def store(self, payroll_indicator_inputs):
        try:
            agreed_deposit_annual = HelperClass().remove_from_string(".", payroll_indicator_inputs['agreed_deposit_annual'])
            agreed_deposit_annual = HelperClass().replace(",", ".", agreed_deposit_annual)

            payroll_agreed_deposit_indicator = PayrollAgreedDepositIndicatorModel()
            payroll_agreed_deposit_indicator.agreed_deposit = agreed_deposit_annual
            payroll_agreed_deposit_indicator.period = payroll_indicator_inputs['period']
            payroll_agreed_deposit_indicator.added_date = datetime.now()
            self.db.add(payroll_agreed_deposit_indicator)
            self.db.commit()
            
            inserted_id = payroll_agreed_deposit_indicator.id

            return inserted_id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"