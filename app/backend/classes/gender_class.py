from app.backend.db.models import GenderModel

class GenderClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(GenderModel).order_by(GenderModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(GenderModel).filter(getattr(GenderModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, gender_inputs):
        try:
            data = GenderModel(**gender_inputs)
            self.db.add(data)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(GenderModel).filter(GenderModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, gender):
        existing_gender = self.db.query(GenderModel).filter(GenderModel.id == id).one_or_none()

        if not existing_gender:
            return "No data found"

        existing_gender_data = gender.dict(exclude_unset=True)
        for key, value in existing_gender_data.items():
            setattr(existing_gender, key, value)

        self.db.commit()

        return 1