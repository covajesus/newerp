from app.backend.db.models import RegionModel

class RegionClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(RegionModel).order_by(RegionModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(RegionModel).filter(getattr(RegionModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, region_inputs):
        try:
            data = RegionModel(**region_inputs)
            self.db.add(data)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(RegionModel).filter(RegionModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, region):
        existing_region = self.db.query(RegionModel).filter(RegionModel.id == id).one_or_none()

        if not existing_region:
            return "No data found"

        existing_region_data = region.dict(exclude_unset=True)
        for key, value in existing_region_data.items():
            setattr(existing_region, key, value)

        self.db.commit()

        return 1