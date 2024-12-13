from app.backend.db.models import PayrollUtmUtaIndicatorModel
from app.backend.classes.helper_class import HelperClass
from datetime import datetime

class PayrollUtmUtaIndicatorClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, period):
        data = self.db.query(PayrollUtmUtaIndicatorModel).filter(PayrollUtmUtaIndicatorModel.period == period).first()

        return data
    
    def store(self, payroll_indicator_inputs):
        try:
            utm_value_current_month = HelperClass().remove_from_string(".", payroll_indicator_inputs['utm_value_current_month'])
            utm_value_current_month = HelperClass().replace(",", ".", utm_value_current_month)
            uta_value_current_month = HelperClass().remove_from_string(".", payroll_indicator_inputs['uta_value_current_month'])
            uta_value_current_month = HelperClass().replace(",", ".", uta_value_current_month)

            payroll_utm_uta_indicator = PayrollUtmUtaIndicatorModel()
            payroll_utm_uta_indicator.utm_value_current_month = utm_value_current_month
            payroll_utm_uta_indicator.uta_value_current_month = uta_value_current_month
            payroll_utm_uta_indicator.period = payroll_indicator_inputs['period']                                                                                                                                                        
            payroll_utm_uta_indicator.added_date = datetime.now()
            self.db.add(payroll_utm_uta_indicator)
            self.db.commit()
            
            inserted_id = payroll_utm_uta_indicator.id

            return inserted_id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"