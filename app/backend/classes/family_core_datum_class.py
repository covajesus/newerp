from app.backend.db.models import FamilyCoreDatumModel
from datetime import datetime
import json

class FamilyCoreDatumClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(FamilyCoreDatumModel).order_by(FamilyCoreDatumModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def get_by_id(self, id):
        data = self.db.query(FamilyCoreDatumModel).filter(FamilyCoreDatumModel.id == id).first()
        if not data:
            return "No data found"
        return data


    def get(self, field, value, one=1):
        try:
            if one == 1:
                data = self.db.query(FamilyCoreDatumModel).filter(getattr(FamilyCoreDatumModel, field) == value).first()
                print(F'FamilyCoreDatumModel: {data}')
                # Serializar los datos de un solo objeto FamilyCoreDatumModel
                serialized_data = {
                    "id": data.id,
                    "family_type_id": data.family_type_id,
                    "employee_rut": data.employee_rut,
                    "gender_id": data.gender_id,
                    "rut": data.rut,
                    "names": data.names,
                    "father_lastname": data.father_lastname,
                    "mother_lastname": data.mother_lastname,
                    "born_date": data.born_date.strftime('%Y-%m-%d') if data.born_date else None,
                    "support": data.support,
                    "added_date": data.added_date.strftime('%Y-%m-%d %H:%M:%S') if data.added_date else None
                }
            else:
                data = self.db.query(FamilyCoreDatumModel).filter(getattr(FamilyCoreDatumModel, field) == value).order_by(FamilyCoreDatumModel.rut).all()
                serialized_data = []
                for item in data:
                    serialized_item = {
                        "id": item.id,
                        "family_type_id": item.family_type_id,
                        "employee_rut": item.employee_rut,
                        "gender_id": item.gender_id,
                        "rut": item.rut,
                        "names": item.names,
                        "father_lastname": item.father_lastname,
                        "mother_lastname": item.mother_lastname,
                        "born_date": item.born_date.strftime('%Y-%m-%d') if item.born_date else None,
                        "support": item.support,
                        "added_date": item.added_date.strftime('%Y-%m-%d %H:%M:%S') if item.added_date else None
                    }
                    serialized_data.append(serialized_item)    

            # Convierte el resultado a una cadena JSON
            serialized_result = json.dumps(serialized_data)

            return serialized_result
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, family_core_datum_inputs, support):
        try:
            family_core_datum = FamilyCoreDatumModel()
            family_core_datum.family_type_id = family_core_datum_inputs.family_type_id
            family_core_datum.employee_rut = family_core_datum_inputs.employee_rut
            family_core_datum.gender_id = family_core_datum_inputs.gender_id
            family_core_datum.rut = family_core_datum_inputs.rut
            family_core_datum.names = family_core_datum_inputs.names
            family_core_datum.father_lastname = family_core_datum_inputs.father_lastname
            family_core_datum.mother_lastname = family_core_datum_inputs.mother_lastname
            family_core_datum.born_date = family_core_datum_inputs.born_date
            family_core_datum.support = support
            family_core_datum.added_date = datetime.now()
            family_core_datum.updated_date = datetime.now()

            self.db.add(family_core_datum)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(FamilyCoreDatumModel).filter(FamilyCoreDatumModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, family_core_datum_inputs, support = None):
        family_core_datum = self.db.query(FamilyCoreDatumModel).filter(FamilyCoreDatumModel.id == id).one_or_none()
        if family_core_datum_inputs.family_type_id != None:
            family_core_datum.family_type_id = family_core_datum_inputs.family_type_id

        if family_core_datum_inputs.gender_id != None:
            family_core_datum.gender_id = family_core_datum_inputs.gender_id

        if family_core_datum_inputs.rut != None:
            family_core_datum.rut = family_core_datum_inputs.rut

        if family_core_datum_inputs.names != None:
            family_core_datum.names = family_core_datum_inputs.names

        if family_core_datum_inputs.father_lastname != None:
            family_core_datum.father_lastname = family_core_datum_inputs.father_lastname

        if family_core_datum_inputs.mother_lastname != None:
            family_core_datum.mother_lastname = family_core_datum_inputs.mother_lastname
        
        if family_core_datum_inputs.born_date != None:
            family_core_datum.born_date = family_core_datum_inputs.born_date

        if support != None and support != "":
            family_core_datum.support = support

        family_core_datum.updated_date = datetime.now()

        self.db.add(family_core_datum)
        
        try:
            self.db.commit()

            return 1
        except Exception as e:
            return 0