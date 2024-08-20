from app.backend.db.models import DocumentEmployeeModel, DocumentEmployeeSignatureModel, EmployeeLaborDatumModel, BranchOfficeModel, SupervisorModel, EmployeeModel, DocumentTypeModel
from datetime import datetime
from sqlalchemy import desc
import json

class ContractClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, rut):
        try:
            data = self.db.query(DocumentEmployeeModel).filter(DocumentEmployeeModel.rut == rut).order_by(DocumentEmployeeModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def supervisor_get_all(self, rut=None, page=1, items_per_page=10):
        try:
            data_query = self.db.query(
                DocumentTypeModel.document_type,
                DocumentEmployeeModel.status_id,
                DocumentEmployeeModel.rut,
                DocumentEmployeeModel.id,
                DocumentEmployeeModel.added_date,
                EmployeeModel.names,
                EmployeeModel.father_lastname,
                EmployeeModel.mother_lastname
            ) \
                .outerjoin(EmployeeLaborDatumModel, EmployeeLaborDatumModel.rut == DocumentEmployeeModel.rut) \
                .outerjoin(EmployeeModel, EmployeeModel.rut == EmployeeLaborDatumModel.rut) \
                .outerjoin(SupervisorModel, SupervisorModel.branch_office_id == EmployeeLaborDatumModel.branch_office_id) \
                .outerjoin(DocumentTypeModel, DocumentTypeModel.id == DocumentEmployeeModel.document_type_id) \
                .filter(SupervisorModel.rut == rut) \
                .filter(DocumentEmployeeModel.status_id == 1) \
                .filter(DocumentTypeModel.document_group_id == 2) \
                .order_by(DocumentEmployeeModel.id.desc())

            total_items = data_query.count()
            total_pages = (total_items + items_per_page - 1) // items_per_page

            if page < 1 or page > total_pages:
                return "Invalid page number"

            data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

            if not data:
                return "No data found"

            # Serializar la lista de resultados en un formato JSON amigable
            serialized_data = {
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "items_per_page": items_per_page,
                "data": [
                    {
                        "document_type": item.document_type,
                        "status_id": item.status_id,
                        "rut": item.rut,
                        "id": item.id,
                        "added_date": item.added_date.strftime('%Y-%m-%d') if item.added_date else None,
                        "names": item.names,
                        "father_lastname": item.father_lastname,
                        "mother_lastname": item.mother_lastname
                    }
                    for item in data
                ]
            }

            serialized_result = json.dumps(serialized_data)

            return serialized_result
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get_all_where(self, document_type_id):
        try:
            data = self.db.query(DocumentEmployeeModel).filter(DocumentEmployeeModel.document_type_id==document_type_id).order_by(DocumentEmployeeModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get(self, field, value):
        try:
            data = self.db.query(DocumentEmployeeModel).filter(getattr(DocumentEmployeeModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, document_employee_inputs):
        try:
            document_employee = DocumentEmployeeModel()
            document_employee.status_id = document_employee_inputs['status_id']
            document_employee.rut = document_employee_inputs['rut']
            document_employee.document_type_id = document_employee_inputs['document_type_id']
            document_employee.added_date = datetime.now()
            document_employee.updated_date = datetime.now()

            self.db.add(document_employee)
            self.db.commit()
            
            return document_employee.id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def medical_license_store(self, document_employee_inputs):
        try:
            document_employee = DocumentEmployeeModel()
            document_employee.status_id = document_employee_inputs.status_id
            document_employee.rut = document_employee_inputs.rut
            document_employee.document_type_id = document_employee_inputs.document_type_id
            document_employee.added_date = datetime.now()
            document_employee.updated_date = datetime.now()

            self.db.add(document_employee)
            self.db.commit()
            
            return document_employee.id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def update_file(self, id, file):
        document_employee = self.db.query(DocumentEmployeeModel).filter(DocumentEmployeeModel.id==id).first()
        document_employee.support = file
        document_employee.status_id = 4
        document_employee.updated_date = datetime.now()

        self.db.add(document_employee)
        self.db.commit()
        
        return 1
    
    def delete(self, id):
        try:
            data = self.db.query(DocumentEmployeeModel).filter(DocumentEmployeeModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, document_employee_inputs):
        document_employee =  self.db.query(DocumentEmployeeModel).filter(DocumentEmployeeModel.id == id).one_or_none()
        
        if 'status_id' in document_employee_inputs and document_employee_inputs['status_id'] is not None:
            document_employee.status_id = document_employee_inputs['status_id']

        if 'rut' in document_employee_inputs and document_employee_inputs['rut'] is not None:
            document_employee.rut = document_employee_inputs['rut']

        if 'document_type_id' in document_employee_inputs and document_employee_inputs['document_type_id'] is not None:
            document_employee.document_type_id = document_employee_inputs['document_type_id']

        if 'old_document_status_id' in document_employee_inputs and document_employee_inputs['old_document_status_id'] is not None:
            document_employee.old_document_status_id = document_employee_inputs['old_document_status_id']

        if 'support' in document_employee_inputs and document_employee_inputs['support'] is not None:
            document_employee.support = document_employee_inputs['support']

        document_employee.update_date = datetime.now()

        self.db.add(document_employee)

        try:
            self.db.commit()

            return 1
        except Exception as e:
            return 0
    
    def sign(self, id):
        document_employee =  self.db.query(DocumentEmployeeModel).filter(DocumentEmployeeModel.id == id).one_or_none()
        document_employee.status_id = 4
        document_employee.updated_date = datetime.now()

        self.db.add(document_employee)
        self.db.commit()

        document_employee_signature = DocumentEmployeeSignatureModel()
        document_employee_signature.document_employee_id = id
        document_employee_signature.rut = document_employee.rut
        document_employee_signature.added_date = datetime.now()
        document_employee_signature.updated_date = datetime.now()

        self.db.add(document_employee_signature)
        self.db.commit()
        
        return 1