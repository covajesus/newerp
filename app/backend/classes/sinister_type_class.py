from app.backend.db.models import SinisterTypeModel
from sqlalchemy.orm import Session

class SinisterTypeClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        """
        Obtiene todos los tipos de siniestros
        """
        try:
            data = self.db.query(SinisterTypeModel).order_by(SinisterTypeModel.sinister_type.asc()).all()
            
            if not data:
                return {"status": "error", "message": "No data found"}
            
            serialized_data = [{
                "id": sinister_type.id,
                "sinister_type": sinister_type.sinister_type,
                "added_date": sinister_type.added_date,
                "updated_date": sinister_type.updated_date
            } for sinister_type in data]
            
            return {"status": "success", "data": serialized_data}
            
        except Exception as e:
            return {"status": "error", "message": f"Error retrieving sinister types: {str(e)}"}
