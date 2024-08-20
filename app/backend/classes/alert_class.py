from app.backend.db.models import AlertModel, AlertTypeModel
import json
from datetime import datetime

class AlertClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, rut=None, page=1, items_per_page=10):
        try:
            if page != 0:

                data_query = self.db.query(AlertModel.id, AlertModel.added_date, AlertTypeModel.alert_type). \
                    outerjoin(AlertTypeModel, AlertTypeModel.id == AlertModel.alert_type_id). \
                    filter(AlertModel.rut == rut). \
                    filter(AlertModel.status_id == 0). \
                    order_by(AlertModel.rut)

                total_items = data_query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return "Invalid page number"

                data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return "No data found"
                            
                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": data
                }
            else:
                data_query = self.db.query(AlertModel).order_by(AlertModel.rut).all()

                return data_query

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(AlertModel).filter(getattr(AlertModel, field) == value).first()

            if data:
                alert_data = data.as_dict()
                serialized_data = json.dumps(alert_data)

                return serialized_data

            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, alert_inputs):
        alert = AlertModel()
        alert.status_id = alert_inputs['status_id']
        alert.alert_type_id = alert_inputs['alert_type_id']
        alert.rut = alert_inputs['rut']
        alert.added_date = datetime.now()

        self.db.add(alert)

        try:
            self.db.commit()

            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(AlertModel).filter(AlertModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, alert_inputs):
        alerts =  self.db.query(AlertModel).filter(AlertModel.rut == id).all()
        
        if alerts:
            for alert in alerts:
                alert_detail =  self.db.query(AlertModel).filter(AlertModel.id == alert.id).first()

                if 'status_id' in alert_inputs and alert_inputs['status_id'] is not None:
                    alert_detail.status_id = alert_inputs['status_id']

                alert_detail.updated_date = datetime.now()
                
            try:
                self.db.commit()
                return len(alerts)
            except Exception as e:
                self.db.rollback()
                return 0
        else:
            return 0