from app.backend.db.models import FamilyTypeModel

class FamilyTypeClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(FamilyTypeModel).order_by(FamilyTypeModel.id).all()
            if not data:
                return "No hay registros"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(FamilyTypeModel).filter(getattr(FamilyTypeModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, FamilyType_inputs):
        try:
            data = FamilyTypeModel(**FamilyType_inputs)
            self.db.add(data)
            self.db.commit()
            return "Registro agregado"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(FamilyTypeModel).filter(FamilyTypeModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return "Registro eliminado"
            else:
                return "No se encontró el registro"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, family_type):
        existing_family_type = self.db.query(FamilyTypeModel).filter(FamilyTypeModel.id == id).one_or_none()

        if not existing_family_type:
            return "No se encontró el registro"

        existing_family_type_data = family_type.dict(exclude_unset=True)
        for key, value in existing_family_type_data.items():
            setattr(existing_family_type, key, value)

        self.db.commit()

        return "Registro actualizado"