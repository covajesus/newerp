from app.backend.db.models import EmployeeModel, EmployeeLaborDatumModel, EmployeeViewModel, ClockUserModel, BranchOfficeModel, OldEmployeeModel, OldEmployeeLaborDatumModel, SupervisorModel, EmployeeLaborDatumModel
from datetime import datetime
from sqlalchemy import func
from app.backend.classes.helper_class import HelperClass
from app.backend.classes.dropbox_class import DropboxClass
import json

class EmployeeClass:
    def __init__(self, db):
        self.db = db

    # Funcion para obtener a todos los empleados sin paginacion
    def get_all_with_no_paginator(self):
        query = self.db.query(EmployeeModel).order_by(EmployeeModel.names).all()

        serialized_data = []
        for employee in query:
            employee_dict = {
                "id": employee.id,
                "rut": employee.rut,
                "visual_rut": employee.visual_rut,
                "names": employee.names,
                "father_lastname": employee.father_lastname,
                "mother_lastname": employee.mother_lastname,
                "gender_id": employee.gender_id,
                "nationality_id": employee.nationality_id,
                "signature_type_id": employee.signature_type_id,
                "personal_email": employee.personal_email,
                "cellphone": employee.cellphone,
                "born_date": str(employee.born_date),
                "picture": employee.picture,
                "signature": employee.signature,
                "added_date": str(employee.added_date),
                "updated_date": str(employee.updated_date)
            }
            serialized_data.append(employee_dict)

        # Devolver la lista serializada
        return json.dumps(serialized_data)

    # Funcion para obtener a todos los empleados con paginacion
    def full_details(self):
        data = self.db.query(EmployeeViewModel).all()

        return data

    # Funcion para obtener a todos los empleados con paginacion
    def get_all(self, rut=None, rol_id=None, page=0, items_per_page=10):
        try:
            if page != 0:
                if rol_id == 3:
                    data_query = self.db.query(EmployeeModel, EmployeeLaborDatumModel, BranchOfficeModel, SupervisorModel). \
                        outerjoin(EmployeeLaborDatumModel, EmployeeLaborDatumModel.rut == EmployeeModel.rut). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == EmployeeLaborDatumModel.branch_office_id). \
                        outerjoin(SupervisorModel, SupervisorModel.branch_office_id == BranchOfficeModel.id). \
                        filter(SupervisorModel.rut == rut). \
                        order_by(EmployeeModel.rut)
                else:
                    data_query = self.db.query(EmployeeModel.id, EmployeeModel.rut, EmployeeModel.visual_rut, EmployeeModel.names, EmployeeModel.father_lastname, EmployeeModel.mother_lastname, EmployeeLaborDatumModel.status_id). \
                        outerjoin(EmployeeLaborDatumModel, EmployeeLaborDatumModel.rut == EmployeeModel.rut). \
                        order_by(EmployeeModel.rut)

                total_items = data_query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return "Invalid page number"

                data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return "No data found"

                # Serializar los datos
                if rol_id == 3:
                    serialized_data = [{
                        "id": employee.id,
                        "rut": employee.rut,
                        "visual_rut": employee.visual_rut,
                        "names": employee.names,
                        "father_lastname": employee.father_lastname,
                        "mother_lastname": employee.mother_lastname,
                        "status_id": employee.status_id,
                    } for employee, labor_datum, branch_office, supervisor in data]
                else:
                    serialized_data = [{
                        "id": employee.id,
                        "rut": employee.rut,
                        "visual_rut": employee.visual_rut,
                        "names": employee.names,
                        "father_lastname": employee.father_lastname,
                        "mother_lastname": employee.mother_lastname,
                        "status_id": employee.status_id,
                    } for employee in data]

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }
            else:
                data_query = self.db.query(EmployeeModel.id, EmployeeModel.rut, EmployeeModel.visual_rut, EmployeeModel.names, EmployeeModel.father_lastname, EmployeeModel.mother_lastname, EmployeeLaborDatumModel.status_id). \
                        outerjoin(EmployeeLaborDatumModel, EmployeeLaborDatumModel.rut == EmployeeModel.rut). \
                        order_by(EmployeeModel.rut).all()

                serialized_data = [{
                    "id": employee.id,
                    "rut": employee.rut,
                    "visual_rut": employee.visual_rut,
                    "names": employee.names,
                    "father_lastname": employee.father_lastname,
                    "mother_lastname": employee.mother_lastname,
                    "status_id": employee.status_id
                } for employee in data_query]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    # Funcion para buscar empleados 
    def search(self, search_inputs, page=1, items_per_page=10):
        if len(search_inputs) > 0:
            search_rut = search_inputs['rut']
            search_names = search_inputs['names']
            search_father_lastname = search_inputs['father_lastname']
            search_mother_lastname = search_inputs['mother_lastname']
            search_status_id = search_inputs['status_id']
            search_branch_office_id = search_inputs['branch_office_id']

        if search_status_id == 2 or search_status_id == 3:
            data_query = self.db.query(OldEmployeeModel).join(OldEmployeeLaborDatumModel, OldEmployeeLaborDatumModel.rut == OldEmployeeModel.rut).add_columns(
                OldEmployeeModel.id,
                OldEmployeeModel.rut,
                OldEmployeeModel.visual_rut,
                OldEmployeeModel.names,
                OldEmployeeModel.father_lastname,
                OldEmployeeModel.mother_lastname,
                OldEmployeeLaborDatumModel.status_id
            ).order_by('rut')

            if len(search_inputs) > 0:
                if search_rut:
                    data_query = data_query.filter(OldEmployeeModel.visual_rut.like(f"%{search_rut}%"))
                if search_names:
                    data_query = data_query.filter(OldEmployeeModel.names.like(f"%{search_names}%"))
                if search_father_lastname:
                    data_query = data_query.filter(OldEmployeeModel.father_lastname.like(f"%{search_father_lastname}%"))
                if search_mother_lastname:
                    data_query = data_query.filter(OldEmployeeModel.mother_lastname.like(f"%{search_mother_lastname}%"))
                if search_branch_office_id:
                    data_query = data_query.filter(OldEmployeeLaborDatumModel.branch_office_id == search_branch_office_id)
                if search_status_id:
                    data_query = data_query.filter(OldEmployeeLaborDatumModel.status_id == search_status_id)
        else:
            data_query = self.db.query(EmployeeModel).join(EmployeeLaborDatumModel, EmployeeLaborDatumModel.rut == EmployeeModel.rut).add_columns(
                EmployeeModel.id,
                EmployeeModel.rut,
                EmployeeModel.visual_rut,
                EmployeeModel.names,
                EmployeeModel.father_lastname,
                EmployeeModel.mother_lastname,
                EmployeeLaborDatumModel.status_id
            ).order_by('rut')

            if len(search_inputs) > 0:
                if search_rut:
                    data_query = data_query.filter(EmployeeModel.visual_rut.like(f"%{search_rut}%"))
                if search_names:
                    data_query = data_query.filter(EmployeeModel.names.like(f"%{search_names}%"))
                if search_father_lastname:
                    data_query = data_query.filter(EmployeeModel.father_lastname.like(f"%{search_father_lastname}%"))
                if search_mother_lastname:
                    data_query = data_query.filter(EmployeeModel.mother_lastname.like(f"%{search_mother_lastname}%"))
                if search_branch_office_id:
                    data_query = data_query.filter(EmployeeLaborDatumModel.branch_office_id == search_branch_office_id)
                if search_status_id:
                    data_query = data_query.filter(EmployeeLaborDatumModel.status_id == search_status_id)

        total_items = data_query.count()
        total_pages = (total_items + items_per_page - 1)

        data = data_query.all()

        if not data:
            return "No data found"

        # Serializar la lista de empleados directamente
        serialized_data = [{
            "id": employee.id,
            "rut": employee.rut,
            "visual_rut": employee.visual_rut,
            "names": employee.names,
            "father_lastname": employee.father_lastname,
            "mother_lastname": employee.mother_lastname,
            "status_id": employee.status_id
        } for employee in data]

        return {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page,
            "items_per_page": items_per_page,
            "data": serialized_data
        }

    def validate_rut(self, rut):
        try:
            data = self.db.query(EmployeeModel).filter(EmployeeModel.rut == rut).count()

            if data != 0:
                return 1
            else:
                return 0
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    # Funcion para obtener un empleado por rut       
    def get(self, field, value):
        try:
            data = self.db.query(EmployeeModel, ClockUserModel.privilege). \
                outerjoin(ClockUserModel, ClockUserModel.rut == EmployeeModel.rut). \
                filter(getattr(EmployeeModel, field) == value). \
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
                    "signature_type_id": data[0].signature_type_id,
                    "personal_email": data[0].personal_email,
                    "cellphone": data[0].cellphone,
                    "born_date": data[0].born_date.strftime('%Y-%m-%d') if data[0].born_date else None,
                    "picture": data[0].picture,
                    "signature": data[0].signature,
                    "privilege": data[1],
                    "added_date": data[0].added_date.strftime('%Y-%m-%d %H:%M:%S') if data[0].added_date else None,
                    "updated_date": data[0].updated_date.strftime('%Y-%m-%d %H:%M:%S') if data[0].updated_date else None
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

    # Funcion para obtener un empleado por rut
    def one_simple_get(self, rut):
        try:
            employee = self.db.query(EmployeeModel).filter(EmployeeModel.rut==rut).first()

            return employee
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    # Funcion para obtener un empleado por rut y verificar si esta activo
    def is_active(self, rut):
        employee = self.db.query(EmployeeModel).filter(EmployeeModel.rut==rut).count()

        return employee
    
    def store(self, employee_inputs):
        numeric_rut = HelperClass().numeric_rut(str(employee_inputs['rut']))

        employee = EmployeeModel()
        employee.rut = numeric_rut
        employee.visual_rut = employee_inputs['rut']
        employee.names = employee_inputs['names']
        employee.father_lastname = employee_inputs['father_lastname']
        employee.mother_lastname = employee_inputs['mother_lastname']
        employee.gender_id = employee_inputs['gender_id']
        employee.nationality_id = employee_inputs['nationality_id']
        employee.personal_email = employee_inputs['personal_email']
        employee.cellphone = employee_inputs['cellphone']
        employee.born_date = employee_inputs['born_date']
        employee.added_date = datetime.now()

        self.db.add(employee)

        try:
            self.db.commit()

            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, rut):
        try:
            data = self.db.query(EmployeeModel).filter(EmployeeModel.rut == rut).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, employee_inputs):
        employee =  self.db.query(EmployeeModel).filter(EmployeeModel.rut == id).first()

        if 'rut' in employee_inputs and employee_inputs['rut'] is not None:
            numeric_rut = HelperClass().numeric_rut(str(employee_inputs['rut']))
            employee.rut = numeric_rut
            employee.visual_rut = employee_inputs['rut']
        
        if 'names' in employee_inputs and employee_inputs['names'] is not None:
            employee.names = employee_inputs['names']
        
        if 'father_lastname' in employee_inputs and employee_inputs['father_lastname'] is not None:
            employee.father_lastname = employee_inputs['father_lastname']
        
        if 'mother_lastname' in employee_inputs and employee_inputs['mother_lastname'] is not None:
            employee.mother_lastname = employee_inputs['mother_lastname']

        if 'gender_id' in employee_inputs and employee_inputs['gender_id'] is not None:
            employee.gender_id = employee_inputs['gender_id']

        if 'nationality_id' in employee_inputs and employee_inputs['nationality_id'] is not None:
            employee.nationality_id = employee_inputs['nationality_id']
        
        if 'personal_email' in employee_inputs and employee_inputs['personal_email'] is not None:
            employee.personal_email = employee_inputs['personal_email']
        
        if 'cellphone' in employee_inputs and employee_inputs['cellphone'] is not None:
            employee.cellphone = employee_inputs['cellphone']
        
        if 'born_date' in employee_inputs and employee_inputs['born_date'] is not None:
            employee.born_date = employee_inputs['born_date']

        if 'signature' in employee_inputs and employee_inputs['signature'] is not None:
            employee.signature = employee_inputs['signature']

        if 'signature_type_id' in employee_inputs and employee_inputs['signature_type_id'] is not None:
            employee.signature_type_id = employee_inputs['signature_type_id']

        if 'picture' in employee_inputs and employee_inputs['picture'] is not None:
            employee.picture = employee_inputs['picture']

        employee.update_date = datetime.now()

        self.db.add(employee)

        try:
            self.db.commit()

            return 1
        except Exception as e:
            return 0
    
    def get_birthdays(self):
        today = datetime.today()

        employees = self.db.query(
            EmployeeModel.rut,
            EmployeeModel.names,
            EmployeeModel.father_lastname,
            BranchOfficeModel.branch_office,
            func.DATE_FORMAT(EmployeeModel.born_date, "%d").label('day'),
            func.DATE_FORMAT(EmployeeModel.born_date, "%M").label('month')
        ) \
        .join(EmployeeLaborDatumModel, EmployeeLaborDatumModel.rut == EmployeeModel.rut) \
        .join(BranchOfficeModel, BranchOfficeModel.id == EmployeeLaborDatumModel.branch_office_id) \
        .filter(func.DAY(EmployeeModel.born_date) >= today.day, func.MONTH(EmployeeModel.born_date) == today.month) \
        .order_by(func.DAY(EmployeeModel.born_date)) \
        .limit(4) \
        .all()

        # Serializar la lista de objetos employees a formato JSON
        serialized_employees = json.dumps([employee._asdict() for employee in employees])

        return serialized_employees
    
    def gender_totals(self):
        men_total = self.db.query(EmployeeModel).filter(EmployeeModel.gender_id == 1).count()
        women_total = self.db.query(EmployeeModel).filter(EmployeeModel.gender_id == 2).count()

        totals = [
            {'gender': 'Men', 'total': men_total},
            {'gender': 'Women', 'total': women_total}
        ]
    
        return totals
    

    def validate_cellphone(self, cellphone):
        existence = self.db.query(EmployeeModel).filter(EmployeeModel.cellphone == cellphone).count()
        employeeExistence = self.db.query(EmployeeModel).filter(EmployeeModel.cellphone == cellphone).first()

        if existence == 1:
            return 1, employeeExistence
        else:
            return 0
