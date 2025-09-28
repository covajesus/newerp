from app.backend.db.models import OldDocumentEmployeeModel, OldEmployeeModel
from sqlalchemy import desc
import json

class OldSalarySettlementClass:
    def __init__(self, db):
        self.db = db
        
    def get(self, field, value, type = 1, page = 1, items_per_page = 10):
        try:
                if type == 1:
                    data = self.db.query(OldDocumentEmployeeModel).filter(getattr(OldDocumentEmployeeModel, field) == value).filter(OldDocumentEmployeeModel.document_type_id == 5).first()
                    if data:
                        return {
                            "added_date": data.added_date.strftime('%Y-%m-%d %H:%M:%S') if data.added_date else None,
                            "document_type_id": data.document_type_id,
                            "support": data.support,
                            "status_id": data.status_id,
                            "id": data.id
                        }
                    else:
                        return "No data found"
                else:
                    data_query = self.db.query(
                        OldDocumentEmployeeModel.added_date,
                        OldDocumentEmployeeModel.document_type_id,
                        OldDocumentEmployeeModel.support,
                        OldDocumentEmployeeModel.status_id,
                        OldDocumentEmployeeModel.id
                    ).outerjoin(OldEmployeeModel, OldEmployeeModel.rut == OldDocumentEmployeeModel.rut).filter(getattr(OldDocumentEmployeeModel, field) == value).filter(OldDocumentEmployeeModel.document_type_id == 5).order_by(desc(OldDocumentEmployeeModel.id))

                    total_items = data_query.count()
                    total_pages = (total_items + items_per_page - 1) // items_per_page

                    if page < 1 or page > total_pages:
                        return "Invalid page number"

                    data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                    if not data:
                        return "No data found"

                    serialized_data = {
                        "total_items": total_items,
                        "total_pages": total_pages,
                        "current_page": page,
                        "items_per_page": items_per_page,
                        "data": [
                            {
                                "added_date": item.added_date.strftime('%Y-%m-%d %H:%M:%S') if item.added_date else None,
                                "document_type_id": item.document_type_id,
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