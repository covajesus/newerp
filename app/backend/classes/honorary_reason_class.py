from app.backend.db.models import HonoraryReasonModel
from sqlalchemy import desc

class HonoraryReasonClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(HonoraryReasonModel).all()

            return data
        
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"