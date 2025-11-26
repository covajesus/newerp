from app.backend.db.models import ZoneModel

class ZoneClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(ZoneModel).order_by(ZoneModel.id).all()
            if not data:
                return "No hay registros"
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
    
    def store(self, Segment_inputs):
        try:
            data = ZoneModel(**Segment_inputs)
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
                return "Registro eliminado"
            else:
                return "No se encontró el registro"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, Segment):
        existing_Segment = self.db.query(ZoneModel).filter(ZoneModel.id == id).one_or_none()

        if not existing_Segment:
            return "No se encontró el registro"

        existing_Segment_data = Segment.dict(exclude_unset=True)
        for key, value in existing_Segment_data.items():
            setattr(existing_Segment, key, value)

        self.db.commit()

        return "Registro actualizado"