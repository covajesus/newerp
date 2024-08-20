from app.backend.db.models import PayrollCcafIndicatorModel
from datetime import datetime

class PayrollCcafIndicatorClass:
    def __init__(self, db):
        self.db = db

    def get(self, period):
        data = self.db.query(PayrollCcafIndicatorModel).filter(PayrollCcafIndicatorModel.period == period).first()

        return data

    def get_all(self, period):
        try:
            data = self.db.query(PayrollCcafIndicatorModel).filter(PayrollCcafIndicatorModel.period == period).first()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def store(self, payroll_indicator_inputs):
        try:
            payroll_ccaf_indicator = PayrollCcafIndicatorModel()
            payroll_ccaf_indicator.ccaf = payroll_indicator_inputs['distribution_7_percent_health_employeer_ccaf']
            payroll_ccaf_indicator.fonasa = payroll_indicator_inputs['distribution_7_percent_health_employeer_fonasa']
            payroll_ccaf_indicator.period = payroll_indicator_inputs['period']
            payroll_ccaf_indicator.added_date = datetime.now()
            self.db.add(payroll_ccaf_indicator)
            self.db.commit()

            inserted_id = payroll_ccaf_indicator.id

            return inserted_id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"