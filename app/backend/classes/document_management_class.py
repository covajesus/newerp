from app.backend.db.models import DocumentEmployeeModel, EmployeeModel, DocumentTypeModel
from datetime import datetime
from sqlalchemy import desc
import json

class DocumentManagementClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, rut, page=1, items_per_page=10):
        try:
            if rut != '':
                data_query = self.db.query(
                    DocumentEmployeeModel.status_id,
                    DocumentEmployeeModel.document_type_id,
                    DocumentEmployeeModel.added_date,
                    DocumentEmployeeModel.support,
                    DocumentEmployeeModel.id
                ) \
                    .filter(DocumentEmployeeModel.rut == rut) \
                    .filter(DocumentEmployeeModel.document_type_id == 4) \
                    .order_by(desc(DocumentEmployeeModel.id))

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
                            "status_id": item.status_id,
                            "document_type_id": item.document_type_id,
                            "added_date": item.added_date.strftime('%Y-%m-%d') if item.added_date else None,
                            "support": item.support,
                            "id": item.id
                        }
                        for item in data
                    ]
                }

                serialized_result = json.dumps(serialized_data)

                return serialized_result
            else:
                data_query = self.db.query(
                    DocumentEmployeeModel.status_id,
                    DocumentEmployeeModel.document_type_id,
                    DocumentEmployeeModel.added_date,
                    DocumentEmployeeModel.support,
                    DocumentEmployeeModel.id,
                    DocumentTypeModel.document_type,
                    EmployeeModel.rut,
                    EmployeeModel.visual_rut,
                    EmployeeModel.names,
                    EmployeeModel.father_lastname,
                    EmployeeModel.mother_lastname
                ) \
                    .outerjoin(EmployeeModel, EmployeeModel.rut == DocumentEmployeeModel.rut) \
                    .outerjoin(DocumentTypeModel, DocumentTypeModel.id == DocumentEmployeeModel.document_type_id) \
                    .filter(DocumentEmployeeModel.status_id <= 2) \
                    .filter(DocumentEmployeeModel.document_type_id == 6) \
                    .order_by(desc(DocumentEmployeeModel.id))

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
                            "status_id": item.status_id,
                            "visual_rut": item.visual_rut,
                            "rut": item.rut,
                            "document_type": item.document_type,
                            "names": item.names,
                            "father_lastname": item.father_lastname,
                            "mother_lastname": item.mother_lastname,
                            "document_type_id": item.document_type_id,
                            "added_date": item.added_date.strftime('%Y-%m-%d') if item.added_date else None,
                            "support": item.support,
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
    
     # Devuelve todos los documentos de la base de datos que contenga el mismo documento_type_id y ordenados por id
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