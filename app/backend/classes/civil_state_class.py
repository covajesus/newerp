from app.backend.db.models import CivilStateModel

class CivilStateClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(CivilStateModel).order_by(CivilStateModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(CivilStateModel).filter(getattr(CivilStateModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, civil_state_inputs):
        try:
            data = CivilStateModel(**civil_state_inputs)
            self.db.add(data)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(CivilStateModel).filter(CivilStateModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, civil_state):
        existing_civil_state = self.db.query(CivilStateModel).filter(CivilStateModel.id == id).one_or_none()

        if not existing_civil_state:
            return "No data found"

        existing_civil_state_data = civil_state.dict(exclude_unset=True)
        for key, value in existing_civil_state_data.items():
            setattr(existing_civil_state, key, value)

        self.db.commit()

        return 1