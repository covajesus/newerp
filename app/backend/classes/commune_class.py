from app.backend.db.models import CommuneModel

class CommuneClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, region_id = ''):
        try:
            if region_id == '':
                data = self.db.query(CommuneModel).order_by(CommuneModel.commune).all()
            else :
                data = self.db.query(CommuneModel).filter(CommuneModel.region_id == region_id).order_by(CommuneModel.commune).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(CommuneModel).filter(getattr(CommuneModel, field) == value).order_by(CommuneModel.commune).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, commune_inputs):
        try:
            data = CommuneModel(**commune_inputs)
            self.db.add(data)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(CommuneModel).filter(CommuneModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, commune):
        existing_commune = self.db.query(CommuneModel).filter(CommuneModel.id == id).one_or_none()

        if not existing_commune:
            return "No data founnd"

        existing_commune_data = commune.dict(exclude_unset=True)
        for key, value in existing_commune_data.items():
            setattr(existing_commune, key, value)

        self.db.commit()

        return 1