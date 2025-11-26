from app.backend.db.models import OldEmployeeExtraModel

class OldEmployeeExtraDatumClass:
    def __init__(self, db):
        self.db = db
        
    def get(self, field, value):
        try:
            data = self.db.query(OldEmployeeExtraModel).filter(getattr(OldEmployeeExtraModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, old_employee_extra_datum_inputs):
        try:
            data = OldEmployeeExtraModel(**old_employee_extra_datum_inputs)
            self.db.add(data)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
