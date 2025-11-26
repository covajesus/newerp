from app.backend.db.models import MeshDatumModel

class MeshDataClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(MeshDatumModel).order_by(MeshDatumModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(MeshDatumModel).filter(getattr(MeshDatumModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, mesh_datum_inputs):
        try:
            data = MeshDatumModel(**mesh_datum_inputs)
            self.db.add(data)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(MeshDatumModel).filter(MeshDatumModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, mesh_datum):
        existing_mesh_datum = self.db.query(MeshDatumModel).filter(MeshDatumModel.id == id).one_or_none()

        if not existing_mesh_datum:
            return "No data found"

        existing_mesh_datum_data = mesh_datum.dict(exclude_unset=True)
        for key, value in existing_mesh_datum_data.items():
            setattr(existing_mesh_datum, key, value)

        self.db.commit()

        return 1