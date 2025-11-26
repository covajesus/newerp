from app.backend.db.models import ContractTypeModel

class ContractTypeClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(ContractTypeModel).order_by(ContractTypeModel.id).all()
            if not data:
                return "No hay registros"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(ContractTypeModel).filter(getattr(ContractTypeModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, contractType_inputs):
        try:
            data = ContractTypeModel(**contractType_inputs)
            self.db.add(data)
            self.db.commit()
            return "Registro agregado"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(ContractTypeModel).filter(ContractTypeModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, contract_type):
        existing_contract_type = self.db.query(ContractTypeModel).filter(ContractTypeModel.id == id).one_or_none()

        if not existing_contract_type:
            return "No data found"

        existing_contract_type_data = contract_type.dict(exclude_unset=True)
        for key, value in existing_contract_type_data.items():
            setattr(existing_contract_type, key, value)

        self.db.commit()

        return 1