from app.backend.db.models import BankModel
import json

class BankClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(BankModel).order_by(BankModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(BankModel).filter(getattr(BankModel, field) == value).first()

            if data:
                # Serializar el objeto BankModel a un diccionario
                bank_data = data.as_dict()

                # Convierte el diccionario a una cadena JSON
                serialized_data = json.dumps(bank_data)

                return serialized_data

            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, Bank_inputs):
        try:
            data = BankModel(**Bank_inputs)
            self.db.add(data)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(BankModel).filter(BankModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, bank):
        existing_bank = self.db.query(BankModel).filter(BankModel.id == id).one_or_none()

        if not existing_bank:
            return "No data found"

        existing_bank_data = bank.dict(exclude_unset=True)
        for key, value in existing_bank_data.items():
            setattr(existing_bank, key, value)

        self.db.commit()

        return 1