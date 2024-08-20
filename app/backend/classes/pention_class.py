from app.backend.db.models import PentionModel

class PentionClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(PentionModel).order_by(PentionModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(PentionModel).filter(getattr(PentionModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, pention_inputs):
        try:
            last_id = self.db.query(PentionModel).order_by(PentionModel.id.desc()).first()
            new_id = last_id.id + 1
            pention_inputs['id'] = new_id
            data = PentionModel(**pention_inputs)
            self.db.add(data)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(PentionModel).filter(PentionModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, pention):
        existing_pention = self.db.query(PentionModel).filter(PentionModel.id == id).one_or_none()

        if not existing_pention:
            return "No data found"

        existing_pention_data = pention.dict(exclude_unset=True)
        for key, value in existing_pention_data.items():
            setattr(existing_pention, key, value)

        self.db.commit()

        return 1