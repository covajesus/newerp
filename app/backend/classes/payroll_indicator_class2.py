from app.backend.db.models import PayrollIndicatorModel
import json
from datetime import datetime

class PayrollIndicatorClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):

        return 1

    def store(self, payroll_indicator_inputs):
        try:
            payroll_indicator = PayrollIndicatorModel()
            payroll_indicator.indicator_id = payroll_indicator_inputs['indicator_id']
            payroll_indicator.indicator_type_id = payroll_indicator_inputs['indicator_type_id']
            payroll_indicator.period = payroll_indicator_inputs['period']
            payroll_indicator.added_date = datetime.now()
            self.db.add(payroll_indicator)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"