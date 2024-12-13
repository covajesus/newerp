from app.backend.db.models import PayrollHeavyDutyQuoteIndicatorModel
from app.backend.classes.helper_class import HelperClass
from datetime import datetime

class PayrollHeavyDutyQuoteIndicatorClass:
    def __init__(self, db):
        self.db = db

    def get(self, duty_type_id, period):
        try:
            data = self.db.query(PayrollHeavyDutyQuoteIndicatorModel).filter(PayrollHeavyDutyQuoteIndicatorModel.duty_type_id == duty_type_id, PayrollHeavyDutyQuoteIndicatorModel.period == period).first()

            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, duty_type_id, payroll_indicator_inputs):
        try:
            if duty_type_id == 1:
                hard_work_porcentage = HelperClass().remove_from_string(".", payroll_indicator_inputs['hard_work_porcentage'])
                hard_work_porcentage = HelperClass().replace(",", ".", hard_work_porcentage)
                hard_work_employeer = HelperClass().remove_from_string(".", payroll_indicator_inputs['hard_work_employeer'])
                hard_work_employeer = HelperClass().replace(",", ".", hard_work_employeer)
                hard_work_worker = HelperClass().remove_from_string(".", payroll_indicator_inputs['hard_work_worker'])
                hard_work_worker = HelperClass().replace(",", ".", hard_work_worker)

                payroll_heavy_duty_quote_indicator = PayrollHeavyDutyQuoteIndicatorModel()
                payroll_heavy_duty_quote_indicator.duty_type_id = 1
                payroll_heavy_duty_quote_indicator.job_position = 1.2
                payroll_heavy_duty_quote_indicator.employer = 1.3
                payroll_heavy_duty_quote_indicator.worker = 1.4
                payroll_heavy_duty_quote_indicator.period = payroll_indicator_inputs['period']
                payroll_heavy_duty_quote_indicator.added_date = datetime.now()
                self.db.add(payroll_heavy_duty_quote_indicator)
                self.db.commit()

            if duty_type_id == 2:
                less_hard_work_porcentage = HelperClass().remove_from_string(".", payroll_indicator_inputs['less_hard_work_porcentage'])
                less_hard_work_porcentage = HelperClass().replace(",", ".", less_hard_work_porcentage)
                less_hard_work_employeer = HelperClass().remove_from_string(".", payroll_indicator_inputs['less_hard_work_employeer'])
                less_hard_work_employeer = HelperClass().replace(",", ".", less_hard_work_employeer)
                less_hard_work_worker = HelperClass().remove_from_string(".", payroll_indicator_inputs['less_hard_work_worker'])
                less_hard_work_worker = HelperClass().replace(",", ".", less_hard_work_worker)

                payroll_heavy_duty_quote_indicator = PayrollHeavyDutyQuoteIndicatorModel()
                payroll_heavy_duty_quote_indicator.duty_type_id = 2
                payroll_heavy_duty_quote_indicator.job_position = 2
                payroll_heavy_duty_quote_indicator.employer = 2
                payroll_heavy_duty_quote_indicator.worker = 2
                payroll_heavy_duty_quote_indicator.period = payroll_indicator_inputs['period']
                payroll_heavy_duty_quote_indicator.added_date = datetime.now()
                self.db.add(payroll_heavy_duty_quote_indicator)
                self.db.commit()

            inserted_id = payroll_heavy_duty_quote_indicator.id

            return inserted_id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"