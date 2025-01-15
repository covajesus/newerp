from app.backend.db.models import ExpenseTypeModel

class ExpenseTypeClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(ExpenseTypeModel). \
                    order_by(ExpenseTypeModel.expense_type). \
                    all()
            
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"