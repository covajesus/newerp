from app.backend.db.models import LetterTypeModel

class LetterTypeClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(LetterTypeModel).order_by(LetterTypeModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(LetterTypeModel).filter(getattr(LetterTypeModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, LetterType_inputs):
        try:
            data = LetterTypeModel(**LetterType_inputs)
            self.db.add(data)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(LetterTypeModel).filter(LetterTypeModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, letter_type):
        existing_letter_type = self.db.query(LetterTypeModel).filter(LetterTypeModel.id == id).one_or_none()

        if not existing_letter_type:
            return "No data found"

        existing_letter_type_data = letter_type.dict(exclude_unset=True)
        for key, value in existing_letter_type_data.items():
            setattr(existing_letter_type, key, value)

        self.db.commit()

        return 1