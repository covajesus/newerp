from app.backend.db.models import OldFamilyCoreDatumModel
from datetime import datetime

class OldFamilyCoreDatumClass:
    def __init__(self, db):
        self.db = db

    def get(self, field, value, one=1):
        try:
            if one == 1:
                data = self.db.query(OldFamilyCoreDatumModel).filter(getattr(OldFamilyCoreDatumModel, field) == value).order_by(OldFamilyCoreDatumModel.rut).first()
            else:
                data = self.db.query(OldFamilyCoreDatumModel).filter(getattr(OldFamilyCoreDatumModel, field) == value).order_by(OldFamilyCoreDatumModel.rut).all()

            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, old_family_core_datum_inputs):
        try:
            old_family_core_datum = OldFamilyCoreDatumModel()
            old_family_core_datum.family_type_id = old_family_core_datum_inputs['family_type_id']
            old_family_core_datum.employee_rut = old_family_core_datum_inputs['employee_rut']
            old_family_core_datum.gender_id = old_family_core_datum_inputs['gender_id']
            old_family_core_datum.rut = old_family_core_datum_inputs['rut']
            old_family_core_datum.names = old_family_core_datum_inputs['names']
            old_family_core_datum.father_lastname = old_family_core_datum_inputs['father_lastname']
            old_family_core_datum.mother_lastname = old_family_core_datum_inputs['mother_lastname']
            old_family_core_datum.born_date = old_family_core_datum_inputs['born_date']
            old_family_core_datum.support = old_family_core_datum_inputs['support']
            old_family_core_datum.added_date = datetime.now()

            self.db.add(old_family_core_datum)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        