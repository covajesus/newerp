from app.backend.db.models import CausalModel
import json


class CausalClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, field, value):
        try:
            data = self.db.query(CausalModel).filter(getattr(CausalModel, field) == value).all()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get(self):
        try:
            data = self.db.query(CausalModel).all()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"