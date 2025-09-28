from app.backend.db.models import PatologyTypeModel

class PatologyTypeClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(PatologyTypeModel).order_by(PatologyTypeModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(PatologyTypeModel).filter(getattr(PatologyTypeModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, PatologyType_inputs):
        try:
            data = PatologyTypeModel(**PatologyType_inputs)
            self.db.add(data)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(PatologyTypeModel).filter(PatologyTypeModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, PatologyType):
        existing_patology_type = self.db.query(PatologyTypeModel).filter(PatologyTypeModel.id == id).one_or_none()

        if not existing_patology_type:
            return "No data found"

        existing_patology_type_data = PatologyType.dict(exclude_unset=True)
        for key, value in existing_patology_type_data.items():
            setattr(existing_patology_type, key, value)

        self.db.commit()

        return 1