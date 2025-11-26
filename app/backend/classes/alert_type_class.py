from app.backend.db.models import AlertTypeModel

class AlertTypeClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(AlertTypeModel).order_by(AlertTypeModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(AlertTypeModel).filter(getattr(AlertTypeModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, AlertType_inputs):
        try:
            data = AlertTypeModel(**AlertType_inputs)
            self.db.add(data)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(AlertTypeModel).filter(AlertTypeModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, alert_type):
        existing_alert_type = self.db.query(AlertTypeModel).filter(AlertTypeModel.id == id).one_or_none()

        if not existing_alert_type:
            return "No data found"

        existing_alert_type_data = alert_type.dict(exclude_unset=True)
        for key, value in existing_alert_type_data.items():
            setattr(existing_alert_type, key, value)

        self.db.commit()

        return 1