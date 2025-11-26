from app.backend.db.models import HolidayModel

class HolidayClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(HolidayModel).order_by(HolidayModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(HolidayModel).filter(getattr(HolidayModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"