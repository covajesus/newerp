from app.backend.db.models import PayrollItemModel
import json
from datetime import datetime

class PayrollItemClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, page = 0, items_per_page=10):
        if page == 0:
            try:
                data = self.db.query(PayrollItemModel).order_by(PayrollItemModel.item.asc()).all()
                if not data:
                    return "No data found"
                serialized_data = []
                for payroll_item in data:
                    serialized_data.append({
                        "id": payroll_item.id,
                        "item_type_id": payroll_item.item_type_id,
                        "classification_id": payroll_item.classification_id,
                        "order_id": payroll_item.order_id,
                        "item": payroll_item.item,
                        "salary_settlement_name": payroll_item.salary_settlement_name,
                        "added_date": payroll_item.added_date,
                        "updated_date": payroll_item.updated_date,
                    })
                return serialized_data
            except Exception as e:
                error_message = str(e)
                return f"Error: {error_message}"
        else:
            try:
                data_query = self.db.query(PayrollItemModel).order_by(PayrollItemModel.id)
                total_items = data_query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page
                if page < 1 or page > total_pages:
                    return "Invalid page number"
                data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()
                if not data:
                    return "No data found"
                serialized_data = []
                for payroll_item in data:
                    serialized_data.append({
                        "id": payroll_item.id,
                    "item_type_id": payroll_item.item_type_id,
                    "item": payroll_item.item,
                    "added_date": payroll_item.added_date,
                    "updated_date": payroll_item.updated_date,
                    })
                return {
                        "total_items": total_items,
                        "total_pages": total_pages,
                        "current_page": page,
                        "items_per_page": items_per_page,
                        "data": serialized_data
                    }
            except Exception as e:
                error_message = str(e)
                return f"Error: {error_message}"
            
    def get_taxable_items(self):
        data = self.db.query(PayrollItemModel).filter(PayrollItemModel.classification_id == 1).all()

        return data
    
    def get_no_taxable_items(self):
        data = self.db.query(PayrollItemModel).filter(PayrollItemModel.classification_id == 2).all()

        return data
    
    def get_legal_discount_items(self):
        data = self.db.query(PayrollItemModel).filter(PayrollItemModel.classification_id == 3).all()

        return data
    
    def get_other_discout_items(self):
        data = self.db.query(PayrollItemModel).filter(PayrollItemModel.classification_id == 4).all()

        return data
    
    def store(self, payroll_item_inputs):
        try:
            data = PayrollItemModel(**payroll_item_inputs)
            self.db.add(data)
            self.db.commit()
            self.db.refresh(data)
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def delete(self, id):
        try:
            data = self.db.query(PayrollItemModel).filter(PayrollItemModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        

    def update(self, id, payroll_item_inputs):
        try:
            data = self.db.query(PayrollItemModel).filter(PayrollItemModel.id == id).first()
            if data:
                data.item_type_id = payroll_item_inputs["item_type_id"]
                data.classification_id = payroll_item_inputs["classification_id"]
                data.order_id = payroll_item_inputs["order_id"]
                data.item = payroll_item_inputs["item"]
                data.salary_settlement_name = payroll_item_inputs["salary_settlement_name"]
                data.updated_date = datetime.now()
                print(data)
                print(payroll_item_inputs)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get(self, id):
        try:
            data = self.db.query(PayrollItemModel).filter(PayrollItemModel.id == id).first()
            if data:
                serialized_data = {
                   "id": data.id,
                   "item_type_id": data.item_type_id,
                   "classification_id": data.classification_id,
                   "order_id": data.order_id,
                   "item": data.item,
                   "salary_settlement_name": data.salary_settlement_name,
                   "added_date": data.added_date,
                   "updated_date": data.updated_date,
                }
                return serialized_data
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"