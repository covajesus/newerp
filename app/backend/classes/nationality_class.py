from app.backend.db.models import NationalityModel
import json

class NationalityClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(NationalityModel).order_by(NationalityModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(NationalityModel).filter(getattr(NationalityModel, field) == value).first()

            if data:
                # Serializar el objeto NationalityModel a un diccionario
                nationality_data = data.as_dict()

                # Convierte el diccionario a una cadena JSON
                serialized_data = json.dumps(nationality_data)

                return serialized_data

            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def store(self, nationality_inputs):
        try:
            data = NationalityModel(**nationality_inputs)
            self.db.add(data)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(NationalityModel).filter(NationalityModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, nationality):
        existing_nationality = self.db.query(NationalityModel).filter(NationalityModel.id == id).one_or_none()

        if not existing_nationality:
            return "No data found"

        existing_nationality_data = nationality.dict(exclude_unset=True)
        for key, value in existing_nationality_data.items():
            setattr(existing_nationality, key, value)

        self.db.commit()

        return 1