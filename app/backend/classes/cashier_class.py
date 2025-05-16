from app.backend.db.models import CashierModel

class CashierClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, branch_office_id = ''):
        try:
            if branch_office_id == '':
                data = self.db.query(CashierModel).order_by(CashierModel.cashier).all()
            else :
                data = self.db.query(CashierModel).filter(CashierModel.branch_office_id == branch_office_id).order_by(CashierModel.cashier).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(CashierModel).filter(getattr(CashierModel, field) == value).order_by(CashierModel.cashier).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def get_subscriber_cashier(self, branch_office_id):
        try:
            data = self.db.query(CashierModel).filter(CashierModel.branch_office_id == branch_office_id).filter(CashierModel.folio_segment_id == 9).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
         
    def get_with_machine(self, id):
        try:
            data = self.db.query(CashierModel).filter(CashierModel.getaway_machine_id == 1). filter(CashierModel.branch_office_id == id).first()
            
            return data.id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"