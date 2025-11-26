from app.backend.db.models import PayrollPeriodModel
from datetime import datetime

class PayrollPeriodClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, page=1, items_per_page=10):
        data_query = self.db.query(PayrollPeriodModel).order_by(PayrollPeriodModel.period.desc())

        total_items = data_query.count()
        total_pages = (total_items + items_per_page - 1) // items_per_page

        if page < 1 or page > total_pages:
            return "Invalid page number"

        data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

        if not data:
            return "No data found"

        # Serializar la lista de empleados directamente
        serialized_data = [{
            "id": period.id,
            "period": period.period,
            "opened": period.opened,
            "closed": period.closed
        } for period in data]

        return {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page,
            "items_per_page": items_per_page,
            "data": serialized_data
        }
            
    def check(self):
        try:
            payroll_opening = self.db.query(PayrollPeriodModel).filter(PayrollPeriodModel.closed == None).first()
            if payroll_opening:
                return payroll_opening.period
            else:
                return 0
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def open(self, open_period_payroll_inputs):
        try:
            self.clean(open_period_payroll_inputs)

            payroll_opening = PayrollPeriodModel()
            payroll_opening.period = open_period_payroll_inputs['period']
            payroll_opening.opened = datetime.now()
            payroll_opening.closed = None
            payroll_opening.added_date = datetime.now()
            payroll_opening.updated_date = datetime.now()

            self.db.add(payroll_opening)
            self.db.commit()
            
            return payroll_opening.id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def close_period(self, open_period_payroll_inputs):
        try:
            period = open_period_payroll_inputs['period']
            payroll_opening = self.db.query(PayrollPeriodModel).filter(PayrollPeriodModel.period == period).first()
            if payroll_opening:
                payroll_opening.closed = datetime.now()
                payroll_opening.updated_date = datetime.now()
                self.db.commit()

            return 1
        except Exception as e:
            error_message = str(e)
            return 0
        
    def clean(self, open_period_payroll_inputs):
        try:
            period = open_period_payroll_inputs['period']
            payroll_opening = self.db.query(PayrollPeriodModel).filter(PayrollPeriodModel.period == period).first()
            if payroll_opening:
                self.db.delete(payroll_opening)
                self.db.commit()

            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"