from app.backend.db.models import PayrollIndicatorModel
from datetime import datetime
import json

class PayrollIndicatorClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, period):
        query = self.db.query(PayrollIndicatorModel).filter(PayrollIndicatorModel.period == period).all()

        serialized_data = []
        for payroll_indicator in query:
            payroll_indicator_dict = {
                "payroll_indicator_id": payroll_indicator.id,
                "indicator_id": payroll_indicator.indicator_id,
                "indicator_type_id": payroll_indicator.indicator_type_id,
                "period": payroll_indicator.period,
                "added_date": payroll_indicator.added_date
            }
            serialized_data.append(payroll_indicator_dict)

        return json.dumps(serialized_data)

    def count(self, period):
        count = self.db.query(PayrollIndicatorModel).filter(PayrollIndicatorModel.period == period).count()

        return count
    
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