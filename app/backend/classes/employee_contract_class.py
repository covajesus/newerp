from app.backend.db.models import DocumentEmployeeModel, EmployeeModel
from sqlalchemy import asc
from app.backend.classes.dropbox_class import DropboxClass
import json

class EmployeeContractClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, rut):
        try:
            data = self.db.query(DocumentEmployeeModel.status_id, DocumentEmployeeModel.added_date, DocumentEmployeeModel.support, DocumentEmployeeModel.rut, DocumentEmployeeModel.id, EmployeeModel.visual_rut, EmployeeModel.names, EmployeeModel.father_lastname, EmployeeModel.mother_lastname). \
                        outerjoin(EmployeeModel, EmployeeModel.id == DocumentEmployeeModel.rut). \
                        filter(DocumentEmployeeModel.rut == rut). \
                        filter(DocumentEmployeeModel.document_type_id == 21). \
                        order_by(asc(DocumentEmployeeModel.id)). \
                        all()
            
            if not data:
                return json.dumps("No data found")
            
            # Convertir los resultados a una lista de diccionarios
            serialized_data = []
            for row in data:
                serialized_row = {
                    "status_id": row.status_id,
                    "support": row.support,
                    "rut": row.rut,
                    "id": row.id,
                    "visual_rut": row.visual_rut,
                    "names": row.names,
                    "father_lastname": row.father_lastname,
                    "mother_lastname": row.mother_lastname
                }
                serialized_data.append(serialized_row)
            
            return json.dumps(serialized_data)
        except Exception as e:
            error_message = str(e)
            return json.dumps(f"Error: {error_message}")

    def download(self, id):
        try:
            data = self.db.query(DocumentEmployeeModel).filter(DocumentEmployeeModel.id == id).first()

            file = DropboxClass(self.db).get('/employee_contracts/', data.support)

            return file
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"