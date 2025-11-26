import json
from sqlalchemy import desc
from app.backend.db.models import  OldDocumentEmployeeModel, OldVacationModel
from datetime import datetime

class OldVacationClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, rut, page=1, items_per_page=10):
        try:
            data_query = self.db.query(OldVacationModel).filter(OldVacationModel.rut == rut)

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
                        "status_id": item.status_id,
                        "document_type_id": item.document_type_id,
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
    
    def store(self, old_vacation_inputs):

        vacation = OldVacationModel()
        vacation.document_employee_id = old_vacation_inputs['document_employee_id']
        vacation.rut = old_vacation_inputs['rut']
        vacation.since = old_vacation_inputs['since']
        vacation.until = old_vacation_inputs['until']
        vacation.days = old_vacation_inputs['days']
        vacation.no_valid_days = old_vacation_inputs['no_valid_days']
        vacation.support = old_vacation_inputs['support']
        vacation.added_date = datetime.now()
        vacation.updated_date = datetime.now()

        self.db.add(vacation)
        try:
            self.db.commit()

            return 1
        except Exception as e:
            return 0
        