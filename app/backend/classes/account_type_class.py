from app.backend.db.models import AccountTypeModel

class AccountTypeClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(AccountTypeModel).order_by(AccountTypeModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(AccountTypeModel).filter(getattr(AccountTypeModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, accountType_inputs):
        try:
            data = AccountTypeModel(**accountType_inputs)
            self.db.add(data)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(AccountTypeModel).filter(AccountTypeModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, account_type):
        existing_account_type = self.db.query(AccountTypeModel).filter(AccountTypeModel.id == id).one_or_none()

        if not existing_account_type:
            return "No data found"

        existing_account_type_data = account_type.dict(exclude_unset=True)
        for key, value in existing_account_type_data.items():
            setattr(existing_account_type, key, value)

        self.db.commit()

        return 1