from app.backend.db.models import SegmentModel

class SegmentClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(SegmentModel).order_by(SegmentModel.id).all()
            if not data:
                return "No hay registros"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(SegmentModel).filter(getattr(SegmentModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, Segment_inputs):
        try:
            data = SegmentModel(**Segment_inputs)
            self.db.add(data)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(SegmentModel).filter(SegmentModel.id == id).first()
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
        existing_Segment = self.db.query(SegmentModel).filter(SegmentModel.id == id).one_or_none()

        if not existing_Segment:
            return "No se encontró el registro"

        existing_Segment_data = Segment.dict(exclude_unset=True)
        for key, value in existing_Segment_data.items():
            setattr(existing_Segment, key, value)

        self.db.commit()

        return "Registro actualizado"