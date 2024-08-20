from app.backend.db.models import ProgressiveVacationModel, DocumentEmployeeModel, EmployeeModel, EmployeeLaborDatumModel, BranchOfficeModel
from app.backend.classes.employee_labor_datum_class import EmployeeLaborDatumClass
from app.backend.classes.employee_extra_datum_class import EmployeeExtraDatumClass
from app.backend.classes.helper_class import HelperClass
from datetime import date
from datetime import datetime
from sqlalchemy import desc
from sqlalchemy import or_
from app.backend.classes.dropbox_class import DropboxClass
import json

class ProgressiveVacationClass:
    def __init__(self, db):
        self.db = db

    #funcion para obtener todos los registros de vacaciones progresivas sin paginacion
    def get_all_with_no_pagination(self, rut):
        try:
            data = (self.db.query(
                        DocumentEmployeeModel.status_id, 
                        DocumentEmployeeModel.document_type_id, 
                        ProgressiveVacationModel.document_employee_id, 
                        DocumentEmployeeModel.support, 
                        ProgressiveVacationModel.rut, 
                        ProgressiveVacationModel.id, 
                        ProgressiveVacationModel.since, 
                        ProgressiveVacationModel.until, 
                        ProgressiveVacationModel.days, 
                        ProgressiveVacationModel.no_valid_days,
                        EmployeeModel.visual_rut,
                        EmployeeModel.names,  
                        EmployeeModel.father_lastname,
                        EmployeeModel.mother_lastname,
                        EmployeeLaborDatumModel.branch_office_id, 
                        BranchOfficeModel.branch_office 
                    )
                    .outerjoin(DocumentEmployeeModel, DocumentEmployeeModel.id == ProgressiveVacationModel.document_employee_id)
                    .join(EmployeeModel, EmployeeModel.rut == DocumentEmployeeModel.rut)
                    .join(EmployeeLaborDatumModel, EmployeeLaborDatumModel.rut == EmployeeModel.rut)
                    .join(BranchOfficeModel, BranchOfficeModel.id == EmployeeLaborDatumModel.branch_office_id)
                    .filter(ProgressiveVacationModel.rut == rut)
                    .filter(DocumentEmployeeModel.document_type_id == 6)
                    .order_by(desc(ProgressiveVacationModel.since))
                    .all())
    
            if not data:
                return "No data found"

            # Convertir los resultados de la consulta en diccionarios
            result = []
            for row in data:
                row_dict = {
                    "status_id": row[0],
                    "document_type_id": row[1],
                    "document_employee_id": row[2],
                    "support": row[3],
                    "rut": row[4],
                    "id": row[5],
                    "since": row[6],
                    "until": row[7],
                    "days": row[8],
                    "no_valid_days": row[9],
                    "visual_rut": row[10],
                    "employee_name": row[11] + " " + row[12] + " " + row[13],  
                    "branch_office_id": row[14],  
                    "branch_office_name": row[15]  
                    }
                result.append(row_dict)

            return result
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def get_all(self, rut, page=1, items_per_page=10):
        try:
            data_query = self.db.query(
                DocumentEmployeeModel.document_type_id,
                DocumentEmployeeModel.status_id,
                ProgressiveVacationModel.document_employee_id,
                DocumentEmployeeModel.support,
                ProgressiveVacationModel.rut,
                ProgressiveVacationModel.id,
                ProgressiveVacationModel.since,
                ProgressiveVacationModel.until,
                ProgressiveVacationModel.days,
                ProgressiveVacationModel.no_valid_days
            ).outerjoin(DocumentEmployeeModel, DocumentEmployeeModel.id == ProgressiveVacationModel.document_employee_id).filter(ProgressiveVacationModel.rut == rut).filter(DocumentEmployeeModel.document_type_id == 36).order_by(desc(ProgressiveVacationModel.since))

            total_items = data_query.count()
            total_pages = (total_items + items_per_page - 1) // items_per_page

            if page < 1 or page > total_pages:
                return "Invalid page number"

            data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

            if not data:
                return "No data found"

            # Serializar los datos en una estructura de diccionario
            serialized_data = {
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "items_per_page": items_per_page,
                "data": [
                    {
                        "document_type_id": item.document_type_id,
                        "status_id": item.status_id,
                        "document_employee_id": item.document_employee_id,
                        "support": item.support,
                        "rut": item.rut,
                        "id": item.id,
                        "since": item.since.strftime('%Y-%m-%d') if item.since else None,
                        "until": item.until.strftime('%Y-%m-%d') if item.until else None,
                        "days": item.days,
                        "no_valid_days": item.no_valid_days
                    }
                    for item in data
                ]
            }

            # Convierte el resultado a una cadena JSON
            serialized_result = json.dumps(serialized_data)

            return serialized_result
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def pdf_get_all(self, rut, page = 1, items_per_page = 10):
        try:
            data_query = self.db.query(
                DocumentEmployeeModel.document_type_id,
                DocumentEmployeeModel.status_id,
                ProgressiveVacationModel.document_employee_id,
                DocumentEmployeeModel.support,
                ProgressiveVacationModel.rut,
                ProgressiveVacationModel.id,
                ProgressiveVacationModel.since,
                ProgressiveVacationModel.until,
                ProgressiveVacationModel.days,
                ProgressiveVacationModel.no_valid_days
            ).outerjoin(DocumentEmployeeModel, DocumentEmployeeModel.id == ProgressiveVacationModel.document_employee_id).filter(ProgressiveVacationModel.rut == rut).filter(DocumentEmployeeModel.document_type_id == 36).order_by(desc(ProgressiveVacationModel.since))

            total_items = data_query.count()
            total_pages = (total_items + items_per_page - 1) // items_per_page

            if page < 1 or page > total_pages:
                return "Invalid page number"

            data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

            if not data:
                return "No data found"

            # Serializar los datos en una estructura de diccionario
            serialized_data = {
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "items_per_page": items_per_page,
                "data": [
                    {
                        "document_type_id": item.document_type_id,
                        "status_id": item.status_id,
                        "document_employee_id": item.document_employee_id,
                        "support": item.support,
                        "rut": item.rut,
                        "id": item.id,
                        "since": item.since.strftime('%Y-%m-%d') if item.since else None,
                        "until": item.until.strftime('%Y-%m-%d') if item.until else None,
                        "days": item.days,
                        "no_valid_days": item.no_valid_days
                    }
                    for item in data
                ]
            }

            # Convierte el resultado a una cadena JSON
            serialized_result = json.dumps(serialized_data)

            return serialized_result
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get(self, field, value):
        try:
            data = self.db.query(ProgressiveVacationModel).filter(getattr(ProgressiveVacationModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, vacation_inputs):
        days = HelperClass().days(vacation_inputs['since'], vacation_inputs['until'], vacation_inputs['no_valid_days'])

        progressive_vacation = ProgressiveVacationModel()
        progressive_vacation.document_employee_id = vacation_inputs['document_employee_id']
        progressive_vacation.rut = vacation_inputs['rut']
        progressive_vacation.since = vacation_inputs['since']
        progressive_vacation.until = vacation_inputs['until']
        progressive_vacation.days = days
        progressive_vacation.no_valid_days = vacation_inputs['no_valid_days']
        progressive_vacation.support = ''
        progressive_vacation.added_date = datetime.now()
        progressive_vacation.updated_date = datetime.now()

        self.db.add(progressive_vacation)
        try:
            self.db.commit()

            return 1
        except Exception as e:
            return 0
        
    def download(self, id):
        try:
            data = self.db.query(DocumentEmployeeModel).filter(DocumentEmployeeModel.id == id).first()

            file = DropboxClass(self.db).get('/employee_documents/', data.support)

            return file
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(ProgressiveVacationModel).filter(ProgressiveVacationModel.document_employee_id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No se encontró el registro"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, vacation):
        existing_vacation = self.db.query(VacationModel).filter(VacationModel.id == id).one_or_none()

        if not existing_vacation:
            return "No se encontró el registro"

        existing_vacation_data = vacation.dict(exclude_unset=True)
        for key, value in existing_vacation_data.items():
            setattr(existing_vacation, key, value)

        self.db.commit()

        return "Registro actualizado"
    
    def legal(self, rut):
        employee_labor_data = EmployeeLaborDatumClass(self.db).get("rut", rut)
        employee_labor_data = json.loads(employee_labor_data)
        employee_labor_data_decoded = employee_labor_data["EmployeeLaborDatumModel"]["entrance_company"]

        employee_extra_data = EmployeeExtraDatumClass(self.db).get("rut", rut)
        months = HelperClass().months(employee_labor_data_decoded, date.today())
        years = HelperClass().months_to_years(months)

        if employee_extra_data.recognized_years != None:
            total_years =  int(years) + int(employee_extra_data.recognized_years)
        else: 
            total_years = years

        progressive_vacation_days = HelperClass().progressive_vacation_days(total_years, employee_extra_data.progressive_vacation_level_id)

        return progressive_vacation_days

    def taken(self, rut):
        progressive_vacations = self.db.query(ProgressiveVacationModel). \
                outerjoin(DocumentEmployeeModel, DocumentEmployeeModel.id == ProgressiveVacationModel.document_employee_id). \
                filter(
                    DocumentEmployeeModel.rut == rut,
                    DocumentEmployeeModel.document_type_id == 36
                ).order_by(desc(DocumentEmployeeModel.added_date)).all()

        taken_days = 0
            
        for progressive_vacation in progressive_vacations:
            if progressive_vacation.no_valid_days is None:
                no_valid_days = 0
            else:
                no_valid_days = progressive_vacation.no_valid_days

            taken_days = taken_days + progressive_vacation.days - no_valid_days

        return taken_days
    