from app.backend.db.models import MedicalLicenseModel, DocumentEmployeeModel, EmployeeModel, EmployeeLaborDatumModel, BranchOfficeModel
from datetime import datetime
from sqlalchemy import desc
from sqlalchemy.sql import func, extract
from app.backend.classes.dropbox_class import DropboxClass
from app.backend.classes.helper_class import HelperClass
import json

class MedicalLicenseClass:
    def __init__(self, db):
        self.db = db

    # Función para obtener todos los registros de licencias médicas de un empleado y sin paginación
    def get_all_with_no_pagination(self, rut):
        try:
            data = (self.db.query(
                        DocumentEmployeeModel.status_id, 
                        DocumentEmployeeModel.document_type_id, 
                        MedicalLicenseModel.document_employee_id, 
                        DocumentEmployeeModel.support, 
                        MedicalLicenseModel.rut, 
                        MedicalLicenseModel.id, 
                        MedicalLicenseModel.since, 
                        MedicalLicenseModel.until, 
                        MedicalLicenseModel.days, 
                        EmployeeModel.visual_rut,
                        EmployeeModel.names,  
                        EmployeeModel.father_lastname,
                        EmployeeModel.mother_lastname,
                        EmployeeLaborDatumModel.branch_office_id, 
                        BranchOfficeModel.branch_office,
                        MedicalLicenseModel.folio
                    )
                    .outerjoin(DocumentEmployeeModel, DocumentEmployeeModel.id == MedicalLicenseModel.document_employee_id)
                    .join(EmployeeModel, EmployeeModel.rut == DocumentEmployeeModel.rut)
                    .join(EmployeeLaborDatumModel, EmployeeLaborDatumModel.rut == EmployeeModel.rut)
                    .join(BranchOfficeModel, BranchOfficeModel.id == EmployeeLaborDatumModel.branch_office_id)
                    .filter(MedicalLicenseModel.rut == rut)
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
                    "since": row[6].strftime('%Y-%m-%d') if row[6] else None,
                    "until": row[7].strftime('%Y-%m-%d') if row[7] else None,
                    "days": row[8],
                    "visual_rut": row[9],
                    "employee_name": row[10] + " " + row[11] + " " + row[12],  
                    "branch_office_id": row[13],  
                    "branch_office_name": row[14] ,
                    "folio": row[15]  
                    }
                result.append(row_dict)

            return result
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def get_all(self):
        try:
            data = self.db.query(MedicalLicenseModel).order_by(MedicalLicenseModel.id).all()
            if not data:
                return "No hay registros"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def verifyLastMonthDayExistenceInLicense(self, rut, period):
        try:
            # Reversión del formato del periodo
            period_parts = period.split('-')
            period = period_parts[1] + '-' + period_parts[0]

            # Consulta a la base de datos
            days = self.db.query(extract('day', MedicalLicenseModel.until)).filter(
                MedicalLicenseModel.rut == rut,
                MedicalLicenseModel.period == period
            ).all()
            
            status = 0
            
            for day in days:
                if period_parts[1] == 1 or period_parts[1] == 3 or period_parts[1] == 5 or period_parts[1] == 7 or period_parts[1] == 8 or period_parts[1] == 10 or period_parts[1] == 12:
                    if day[0] == 31:
                        status = 1

                if period_parts[1] == 2:
                    if day[0] == 28 or day[0] == 29:
                        status = 1
                    
            return status
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

        
    def how_many_medical_license_days(self, rut, period):
        since = str(period) + '-01'

        last_day_month = HelperClass.get_last_day_of_month(since)
        until = str(period) + '-' + str(last_day_month)

        try:
            # Realizar una consulta para sumar los días de vacaciones dentro del rango especificado
            total_days = self.db.query(func.sum(MedicalLicenseModel.days)).\
                filter(MedicalLicenseModel.rut == rut).\
                filter(MedicalLicenseModel.since >= since).\
                filter(MedicalLicenseModel.since <= until).scalar()
            
            verification_status = self.verifyLastMonthDayExistenceInLicense(rut, period)

            # Si no hay licencias en el rango, total_days puede ser None, en ese caso, convertirlo a 0
            if total_days == None:
                total_days = 0
            else:
                if verification_status == 1 and last_day_month == 31:
                    total_days = int(total_days) - 1
                elif verification_status == 1 and last_day_month == 28:
                    total_days = int(total_days) + 2
                elif verification_status == 1 and last_day_month == 29:
                    total_days = int(total_days) + 1
                
            return total_days
        
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value, type=1, page=1, items_per_page=10):
        try:
            if type == 1:
                data = self.db.query(MedicalLicenseModel, DocumentEmployeeModel). \
                        outerjoin(DocumentEmployeeModel, DocumentEmployeeModel.id == MedicalLicenseModel.document_employee_id). \
                        filter(MedicalLicenseModel.id == value). \
                        first()

                if data:
                    # Serializar el objeto MedicalLicenseModel a un diccionario
                    serialized_data = {
                        "document_employee_id": data.DocumentEmployeeModel.id,
                        "document_type_id": data.DocumentEmployeeModel.document_type_id,
                        "folio": data.MedicalLicenseModel.folio,
                        "since": data.MedicalLicenseModel.since.strftime('%Y-%m-%d') if data.MedicalLicenseModel.since else None,
                        "until": data.MedicalLicenseModel.until.strftime('%Y-%m-%d') if data.MedicalLicenseModel.until else None,
                        "days": data.MedicalLicenseModel.days,
                        "support": data.DocumentEmployeeModel.support,
                        "status_id": data.DocumentEmployeeModel.status_id,
                        "id": data.MedicalLicenseModel.id
                    }

                    return serialized_data
                else:
                    return "No data found"
            else:
                data_query = self.db.query(
                    MedicalLicenseModel.document_employee_id,
                    DocumentEmployeeModel.document_type_id,
                    MedicalLicenseModel.folio,
                    EmployeeModel.visual_rut,
                    MedicalLicenseModel.since,
                    MedicalLicenseModel.until,
                    MedicalLicenseModel.days,
                    DocumentEmployeeModel.support,
                    DocumentEmployeeModel.status_id,
                    MedicalLicenseModel.id
                ).outerjoin(DocumentEmployeeModel, DocumentEmployeeModel.id == MedicalLicenseModel.document_employee_id).outerjoin(EmployeeModel, EmployeeModel.rut == MedicalLicenseModel.rut).filter(getattr(MedicalLicenseModel, field) == value).filter(DocumentEmployeeModel.document_type_id == 35).order_by(desc(MedicalLicenseModel.since))

                total_items = data_query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return "Invalid page number"

                data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return "No data found"

                # Serializar la lista de objetos MedicalLicenseModel a una lista de diccionarios
                serialized_data = {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": [
                        {
                            "document_employee_id": item.document_employee_id,
                            "document_type_id": item.document_type_id,
                            "folio": item.folio,
                            "visual_rut": item.visual_rut,
                            "since": item.since.strftime('%Y-%m-%d') if item.since else None,
                            "until": item.until.strftime('%Y-%m-%d') if item.until else None,
                            "days": item.days,
                            "support": item.support,
                            "status_id": item.status_id,
                            "id": item.id
                        }
                        for item in data
                    ]
                }

                serialized_result = json.dumps(serialized_data)

                return serialized_result
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, medical_license_inputs, document_employee_id):
        try:
            get_periods = HelperClass().get_periods(medical_license_inputs['since'], medical_license_inputs['until'])

            for i in range(len(get_periods)):
                period = HelperClass().split(get_periods[i][0], '-')
                period = period[1] +'-'+ period[0]

                medical_license = MedicalLicenseModel()
                medical_license.document_employee_id = document_employee_id
                medical_license.medical_license_type_id = medical_license_inputs['medical_license_type_id']
                medical_license.patology_type_id = medical_license_inputs['patology_type_id']
                medical_license.period = period
                medical_license.rut = medical_license_inputs['rut']
                medical_license.folio = medical_license_inputs['folio']
                medical_license.since = get_periods[i][0]
                medical_license.until = get_periods[i][1]
                medical_license.days = get_periods[i][2]
                medical_license.added_date = datetime.now()
                medical_license.updated_date = datetime.now()

                self.db.add(medical_license)
                self.db.commit()

            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(MedicalLicenseModel).filter(MedicalLicenseModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No se encontró el registro"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, medical_license):
        existing_medical_license = self.db.query(MedicalLicenseModel).filter(MedicalLicenseModel.id == id).one_or_none()

        if not existing_medical_license:
            return "No se encontró el registro"

        existing_medical_license_data = medical_license.dict(exclude_unset=True)
        for key, value in existing_medical_license_data.items():
            setattr(existing_medical_license, key, value)

        self.db.commit()

        return "Registro actualizado"
    
    def download(self, id):
        try:
            # Assuming 'added_date' is a datetime field
            data = self.db.query(DocumentEmployeeModel).filter(DocumentEmployeeModel.id == id).first()

            if data and data.added_date > datetime(2023, 12, 31, 0, 0, 0):
                file_path = '/medical_licenses/'
            else:
                file_path = '/employee_documents/'

            # Check if the 'data' object exists before using it
            if data:
                file = DropboxClass(self.db).get(file_path, data.support)
                return file
            else:
                return "Error: Document not found"

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"