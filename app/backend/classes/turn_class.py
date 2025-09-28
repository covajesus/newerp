from app.backend.db.models import TurnModel
import json
from sqlalchemy import or_
class TurnClass:
    def __init__(self, db):
        self.db = db


    def get_by_group(self, group_id):
        try:
            data = self.db.query(TurnModel).filter(TurnModel.group_id == group_id).all()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def get_all(self):
        try:
            data = self.db.query(TurnModel).all()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get(self, employee_type_id, group_id, search_term=None):
        try:
            query = self.db.query(TurnModel).\
                filter(TurnModel.employee_type_id == employee_type_id, TurnModel.group_id == group_id)
            
            if search_term and search_term != "Buscar Turno":
                # Asume que `turn` es el campo que quieres buscar
                query = query.filter(or_(TurnModel.turn.contains(search_term)))
            
            data = query.all()
            
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"