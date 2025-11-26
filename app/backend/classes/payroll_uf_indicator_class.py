from app.backend.db.models import PayrollUfIndicatorModel
from app.backend.classes.helper_class import HelperClass
import json
from datetime import datetime

class PayrollUfIndicatorClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, period):
        data = self.db.query(PayrollUfIndicatorModel).filter(PayrollUfIndicatorModel.period == period).first()

        return data
    
    def get(self, period):
        data = self.db.query(PayrollUfIndicatorModel).filter(PayrollUfIndicatorModel.period == period).first()

        return data

    def store(self, payroll_indicator_inputs):
        try:
            uf_value_current_month = HelperClass().remove_from_string(".", payroll_indicator_inputs['uf_value_current_month'])
            uf_value_current_month = HelperClass().replace(",", ".", uf_value_current_month)
            uf_value_last_month = HelperClass().remove_from_string(".", payroll_indicator_inputs['uf_value_last_month'])
            uf_value_last_month = HelperClass().replace(",", ".", uf_value_last_month)

            payroll_uf_indicator = PayrollUfIndicatorModel()
            payroll_uf_indicator.uf_value_current_month = uf_value_current_month
            payroll_uf_indicator.uf_value_last_month = uf_value_last_month
            payroll_uf_indicator.period = payroll_indicator_inputs['period']
            payroll_uf_indicator.added_date = datetime.now()
            self.db.add(payroll_uf_indicator)
            self.db.commit()

            inserted_id = payroll_uf_indicator.id

            return inserted_id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"