from app.backend.db.models import OldEmployeeModel ,  ClockUserModel
from datetime import datetime
from sqlalchemy import func
from app.backend.classes.helper_class import HelperClass
from app.backend.classes.dropbox_class import DropboxClass
import json

class OldEmployeeClass:
    def __init__(self, db):
        self.db = db

    def get(self, field, value):
        try:
            data = self.db.query(OldEmployeeModel, ClockUserModel.privilege). \
                outerjoin(ClockUserModel, ClockUserModel.rut == OldEmployeeModel.rut). \
                filter(getattr(OldEmployeeModel, field) == value). \
                first()

            if data:
                # Serializar los datos del empleado
                employee_data = {
                    "id": data[0].id,
                    "rut": data[0].rut,
                    "visual_rut": data[0].visual_rut,
                    "names": data[0].names,
                    "father_lastname": data[0].father_lastname,
                    "mother_lastname": data[0].mother_lastname,
                    "gender_id": data[0].gender_id,
                    "nationality_id": data[0].nationality_id,
                    "personal_email": data[0].personal_email,
                    "cellphone": data[0].cellphone,
                    "born_date": data[0].born_date.strftime('%Y-%m-%d') if data[0].born_date else None,
                    "picture": data[0].picture,
                    "privilege": data[1]
                }

                # Serializar la firma (signature) y la imagen (picture)
                signature = DropboxClass(self.db).get('/signatures/', str(data[0].signature)) if data[0].signature else None
                picture = DropboxClass(self.db).get('/pictures/', str(data[0].picture)) if data[0].picture else None

                # Crear el resultado final como un diccionario
                result = {
                    "employee_data": employee_data,
                    "signature": signature,
                    "picture": picture,
                }

                # Convierte el resultado a una cadena JSON
                serialized_result = json.dumps(result)

                return serialized_result

            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    

    def store(self, old_employee_inputs):
        numeric_rut = HelperClass().numeric_rut(str(old_employee_inputs['rut']))
        
        employee = OldEmployeeModel()
        employee.rut = numeric_rut
        employee.visual_rut = old_employee_inputs['visual_rut']
        employee.names = old_employee_inputs['names']
        employee.father_lastname = old_employee_inputs['father_lastname']
        employee.mother_lastname = old_employee_inputs['mother_lastname']
        employee.gender_id = old_employee_inputs['gender_id']
        employee.nationality_id = old_employee_inputs['nationality_id']
        employee.personal_email = old_employee_inputs['personal_email']
        employee.cellphone = old_employee_inputs['cellphone']
        employee.born_date = old_employee_inputs['born_date']
        employee.added_date = datetime.now()

        self.db.add(employee)

        try:
            self.db.commit()

            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"