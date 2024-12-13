from app.backend.db.models import MedicalLicenseTypeModel

class MedicalLicenseTypeClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(MedicalLicenseTypeModel).order_by(MedicalLicenseTypeModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(MedicalLicenseTypeModel).filter(getattr(MedicalLicenseTypeModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, MedicalLicenseType_inputs):
        try:
            data = MedicalLicenseTypeModel(**MedicalLicenseType_inputs)
            self.db.add(data)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(MedicalLicenseTypeModel).filter(MedicalLicenseTypeModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, medical_license_type):
        existing_medical_license_type = self.db.query(MedicalLicenseTypeModel).filter(MedicalLicenseTypeModel.id == id).one_or_none()

        if not existing_medical_license_type:
            return "No data found"

        existing_medical_license_type_data = medical_license_type.dict(exclude_unset=True)
        for key, value in existing_medical_license_type_data.items():
            setattr(existing_medical_license_type, key, value)

        self.db.commit()

        return 1