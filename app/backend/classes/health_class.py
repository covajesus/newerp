from app.backend.db.models import HealthModel

class HealthClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(HealthModel).order_by(HealthModel.health).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(HealthModel).filter(getattr(HealthModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, health_inputs):
        try:
            data = HealthModel(**health_inputs)
            self.db.add(data)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(HealthModel).filter(HealthModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, health):
        existing_health = self.db.query(HealthModel).filter(HealthModel.id == id).one_or_none()

        if not existing_health:
            return "No data found"

        existing_health_data = health.dict(exclude_unset=True)
        for key, value in existing_health_data.items():
            setattr(existing_health, key, value)

        self.db.commit()

        return 1