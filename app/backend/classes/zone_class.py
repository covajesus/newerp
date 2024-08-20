from app.backend.db.models import ZoneModel

class ZoneClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(ZoneModel).order_by(ZoneModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(ZoneModel).filter(getattr(ZoneModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, zone_inputs):
        try:
            data = ZoneModel(**zone_inputs)
            self.db.add(data)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(ZoneModel).filter(ZoneModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, zone):
        existing_zone = self.db.query(ZoneModel).filter(ZoneModel.id == id).one_or_none()

        if not existing_zone:
            return "No data found"

        existing_zone_data = zone.dict(exclude_unset=True)
        for key, value in existing_zone_data.items():
            setattr(existing_zone, key, value)

        self.db.commit()

        return 1