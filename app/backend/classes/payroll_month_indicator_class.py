from app.backend.db.models import PayrollMonthIndicatorModel
from datetime import datetime

class PayrollMonthIndicatorClass:
    def __init__(self, db):
        self.db = db

    def get(self, month_id, period):
        data = self.db.query(PayrollMonthIndicatorModel).filter(PayrollMonthIndicatorModel.month_id == month_id).filter(PayrollMonthIndicatorModel.period == period).first()

        return data

    def store(self, month_id, payroll_month_indicator_inputs):
        try:
            if month_id == 1:
                payroll_month_indicator = PayrollMonthIndicatorModel()
                payroll_month_indicator.month_id = month_id
                payroll_month_indicator.month_value = payroll_month_indicator_inputs['month_value_1']
                payroll_month_indicator.period = payroll_month_indicator_inputs['period']
                payroll_month_indicator.added_date = datetime.now()
                self.db.add(payroll_month_indicator)
                self.db.commit()
            elif month_id == 2:
                payroll_month_indicator = PayrollMonthIndicatorModel()
                payroll_month_indicator.month_id = month_id
                payroll_month_indicator.month_value = payroll_month_indicator_inputs['month_value_2']
                payroll_month_indicator.period = payroll_month_indicator_inputs['period']
                payroll_month_indicator.added_date = datetime.now()
                self.db.add(payroll_month_indicator)
                self.db.commit()
            elif month_id == 3:
                payroll_month_indicator = PayrollMonthIndicatorModel()
                payroll_month_indicator.month_id = month_id
                payroll_month_indicator.month_value = payroll_month_indicator_inputs['month_value_3']
                payroll_month_indicator.period = payroll_month_indicator_inputs['period']
                payroll_month_indicator.added_date = datetime.now()
                self.db.add(payroll_month_indicator)
                self.db.commit()

            inserted_id = payroll_month_indicator.id

            return inserted_id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"