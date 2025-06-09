from app.backend.db.models import GroupDetailModel
from datetime import datetime
import json
from sqlalchemy.orm import Session
from sqlalchemy.dialects import mysql

class GroupDetailClass:
    def __init__(self, db):
        self.db = db

    def get(self, id):
        try:
            data_query = self.db.query(GroupDetailModel.id, GroupDetailModel.group_detail).filter(GroupDetailModel.id == id).first()

            if data_query:
                # Serializar los datos del empleado
                group_detail_data = {
                    "id": id,
                    "group_detail": data_query.group_detail
                }

                result = {
                    "group_detail_data": group_detail_data
                }

                # Convierte el resultado a una cadena JSON
                serialized_result = json.dumps(result)

                return serialized_result
            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def get_list(self):
        try:
            data = self.db.query(GroupDetailModel). \
                    order_by(GroupDetailModel.group_detail). \
                    all()
            
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get_all(self, page = 1, items_per_page = 10):
        try:

            # Construir la consulta base con los filtros aplicados
            query = self.db.query(
                GroupDetailModel.id, 
                GroupDetailModel.group_detail
            ).order_by(
                GroupDetailModel.group_detail
            )

            # Si se solicita paginación
            if page > 0:
                # Calcular el total de registros
                total_items = query.count()
                print(query.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))

                total_pages = (total_items + items_per_page - 1) // items_per_page
                print(total_pages)
                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                # Aplicar paginación en la consulta
                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                # Serializar los datos
                serialized_data = [{
                    "id": group_detail.id,
                    "group_detail": group_detail.group_detail
                } for group_detail in data]

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
                    "id": group_detail.id,
                    "group_detail": group_detail.group_detail
                } for group_detail in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
        
    def get(self, id):
        try:
            data = self.db.query(GroupDetailModel). \
                    filter(GroupDetailModel.id == id). \
                    first()
            
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def store(self, group_detail_inputs):
        group_detail = GroupDetailModel(
                group_detail=group_detail_inputs.group_detail
            )

        self.db.add(group_detail)

        try:
            self.db.commit()
            return "Geroup detail stored successfully"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            self.db.query(GroupDetailModel).filter(GroupDetailModel.id == id).delete()
            self.db.commit()

            return {"status": "success", "message": "Group detail deleted successfully"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def update(self, update_expense_type_inputs):
        try:
            group_detail = self.db.query(GroupDetailModel).filter(
                GroupDetailModel.id == update_expense_type_inputs.id
            ).first()

            if group_detail:
                group_detail.group_detail = update_expense_type_inputs.group_detail
                self.db.commit()
                return "Group detail updated successfully"
            else:
                return "Group detail not found"

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"