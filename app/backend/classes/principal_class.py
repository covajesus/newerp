from app.backend.db.models import PrincipalModel

class PrincipalClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(PrincipalModel).order_by(PrincipalModel.principal).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(PrincipalModel).filter(getattr(PrincipalModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, principal_inputs):
        try:
            data = PrincipalModel(**principal_inputs)
            self.db.add(data)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(PrincipalModel).filter(PrincipalModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, principal):
        existing_principal = self.db.query(PrincipalModel).filter(PrincipalModel.id == id).one_or_none()

        if not existing_principal:
            return "No data found"

        existing_principal_data = principal.dict(exclude_unset=True)
        for key, value in existing_principal_data.items():
            setattr(existing_principal, key, value)

        self.db.commit()

        return 1