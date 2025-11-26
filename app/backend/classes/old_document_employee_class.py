from app.backend.db.models import OldDocumentEmployeeModel
from datetime import datetime
from sqlalchemy import desc
import json

class OldDocumentEmployeeClass:
    def __init__(self, db):
        self.db = db
        
    def get(self, field, value):
        try:
            data = self.db.query(OldDocumentEmployeeModel).filter(getattr(OldDocumentEmployeeModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, old_document_employee_inputs):
        try:
            document_employee = OldDocumentEmployeeModel()
            document_employee.status_id = old_document_employee_inputs['status_id']
            document_employee.rut = old_document_employee_inputs['rut']
            document_employee.document_type_id = old_document_employee_inputs['document_type_id']
            document_employee.support = old_document_employee_inputs['support']
            document_employee.added_date = datetime.now()
            document_employee.updated_date = datetime.now()

            self.db.add(document_employee)
            self.db.commit()
            
            return document_employee.id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        