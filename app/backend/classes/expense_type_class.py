from app.backend.db.models import ExpenseTypeModel
from datetime import datetime
import json

class ExpenseTypeClass:
    def __init__(self, db):
        self.db = db

    def get(self, id):
        try:
            data_query = self.db.query(ExpenseTypeModel.type, ExpenseTypeModel.group_detail, ExpenseTypeModel.expense_type, ExpenseTypeModel.accounting_account, ExpenseTypeModel.capitulation_visibility_id, ExpenseTypeModel.eerr_visibility_id, ExpenseTypeModel.track_visibility_id).filter(ExpenseTypeModel.id == id).first()

            if data_query:
                # Serializar los datos del empleado
                collection_data = {
                    "id": id,
                    "expense_type": data_query.expense_type,
                    "accounting_account": data_query.accounting_account,
                    "capitulation_visibility_id": data_query.capitulation_visibility_id,
                    "eerr_visibility_id": data_query.eerr_visibility_id,
                    "track_visibility_id": data_query.track_visibility_id,
                    "type": data_query.type,
                    "group_detail": data_query.group_detail
                }

                result = {
                    "expense_type__data": collection_data
                }

                # Convierte el resultado a una cadena JSON
                serialized_result = json.dumps(result)

                return serialized_result
            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get_list(self, page=0, items_per_page=10):
        try:
            # Construir la consulta base con los filtros aplicados
            query = self.db.query(
                ExpenseTypeModel.id,
                ExpenseTypeModel.expense_type
            ).order_by(
                ExpenseTypeModel.expense_type
            )

            # Si se solicita paginación
            if page > 0:
                # Calcular el total de registros
                total_items = query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                # Aplicar paginación en la consulta
                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                # Serializar los datos
                serialized_data = [{
                    "id": expense_type.id,
                    "expense_type": expense_type.expense_type,
                } for expense_type in data]

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }

            # Si no se solicita paginación, traer todos los datos
            else:
                data = query.all()

                # Serializar los datos
                serialized_data = [{
                    "id": expense_type.id,
                    "expense_type": expense_type.expense_type
                } for expense_type in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
        
    def get_all(self):
        try:
            data = self.db.query(ExpenseTypeModel). \
                    order_by(ExpenseTypeModel.expense_type). \
                    all()
            
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get_all_capitulation_visibles(self):
        try:
            data = self.db.query(ExpenseTypeModel). \
                    filter(ExpenseTypeModel.capitulation_visibility_id == 1). \
                    order_by(ExpenseTypeModel.expense_type). \
                    all()
            
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get_all_eerr_visibles(self):
        try:
            data = self.db.query(ExpenseTypeModel). \
                    filter(ExpenseTypeModel.eerr_visibility_id == 1). \
                    order_by(ExpenseTypeModel.expense_type). \
                    all()
            
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get(self, id):
        try:
            data = self.db.query(ExpenseTypeModel). \
                    filter(ExpenseTypeModel.id == id). \
                    first()
            
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def store(self, expense_type_inputs):
        expense_type = ExpenseTypeModel(
                expense_type=expense_type_inputs.expense_type,
                accounting_account=expense_type_inputs.accounting_account,
                capitulation_visibility_id=expense_type_inputs.capitulation_visibility_id,
                eerr_visibility_id=expense_type_inputs.eerr_visibility_id,
                track_visibility_id=expense_type_inputs.track_visibility_id,
                type=expense_type_inputs.type,
                group_detail=expense_type_inputs.group_detail
            )

        self.db.add(expense_type)

        try:
            self.db.commit()
            return "Expense type stored successfully"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            self.db.query(ExpenseTypeModel).filter(ExpenseTypeModel.id == id).delete()
            self.db.commit()

            return {"status": "success", "message": "Expense type deleted successfully"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def update(self, update_expense_type_inputs):
        try:
            expense_type = self.db.query(ExpenseTypeModel).filter(
                ExpenseTypeModel.id == update_expense_type_inputs.id
            ).first()

            if expense_type:
                expense_type.expense_type = update_expense_type_inputs.expense_type
                expense_type.accounting_account = update_expense_type_inputs.accounting_account
                expense_type.capitulation_visibility_id = update_expense_type_inputs.capitulation_visibility_id
                expense_type.eerr_visibility_id = update_expense_type_inputs.eerr_visibility_id
                expense_type.track_visibility_id = update_expense_type_inputs.track_visibility_id
                expense_type.type = update_expense_type_inputs.type
                expense_type.group_detail = update_expense_type_inputs.group_detail

                self.db.commit()
                return "Expense type updated successfully"
            else:
                return "Expense type not found"

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"