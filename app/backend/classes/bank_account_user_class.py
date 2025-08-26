from app.backend.db.models import BankAccountUserModel
from datetime import datetime
from app.backend.classes.helper_class import HelperClass
import json

class BankAccountUserClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, id, page=0, items_per_page=10):
        try:
            # Construir la consulta base
            query = self.db.query(
                BankAccountUserModel.id,
                BankAccountUserModel.user_id,
                BankAccountUserModel.rut,
                BankAccountUserModel.bank_account_name,
                BankAccountUserModel.bank_account_type_id,
                BankAccountUserModel.bank_account_number,
                BankAccountUserModel.bank_account_email,
                BankAccountUserModel.added_date
            ).filter(BankAccountUserModel.user_id == id).order_by(
                BankAccountUserModel.id.desc()
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
                    "id": item.id,
                    "rut": item.rut,
                    "bank_account_name": item.bank_account_name,
                    "bank_account_type_id": item.bank_account_type_id,
                    "bank_account_number": item.bank_account_number,
                    "bank_account_email": item.bank_account_email,
                    "added_date": item.added_date.strftime('%Y-%m-%d') if item.added_date else None
                } for item in data]

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
                    "id": item.id,
                    "rut": item.rut,
                    "bank_account_name": item.bank_account_name,
                    "bank_account_type_id": item.bank_account_type_id,
                    "bank_account_number": item.bank_account_number,
                    "bank_account_email": item.bank_account_email,
                    "added_date": item.added_date.strftime('%Y-%m-%d') if item.added_date else None
                } for item in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}

    def get(self, id):
        try:
            data_query = self.db.query(BankAccountUserModel).filter(BankAccountUserModel.id == id).first()

            if data_query:
                # Serializar los datos
                bank_account_user_data = {
                    "id": data_query.id,
                    "rut": data_query.rut,
                    "bank_account_name": data_query.bank_account_name,
                    "bank_account_type_id": data_query.bank_account_type_id,
                    "bank_account_number": data_query.bank_account_number,
                    "bank_account_email": data_query.bank_account_email,
                    "added_date": data_query.added_date.strftime('%Y-%m-%d %H:%M:%S') if data_query.added_date else None,
                    "updated_date": data_query.updated_date.strftime('%Y-%m-%d %H:%M:%S') if data_query.updated_date else None
                }

                result = {
                    "bank_account_user_data": bank_account_user_data
                }

                serialized_result = json.dumps(result)
                return serialized_result
            else:
                return "No se encontraron datos para el ID especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def get_by_rut(self, rut):
        try:
            data_query = self.db.query(BankAccountUserModel).filter(BankAccountUserModel.rut == rut).all()

            if data_query:
                # Serializar los datos
                serialized_data = [{
                    "id": item.id,
                    "user_id": item.user_id,
                    "rut": item.rut,
                    "bank_account_name": item.bank_account_name,
                    "bank_account_type_id": item.bank_account_type_id,
                    "bank_account_number": item.bank_account_number,
                    "bank_account_email": item.bank_account_email,
                    "added_date": item.added_date.strftime('%Y-%m-%d %H:%M:%S') if item.added_date else None,
                    "updated_date": item.updated_date.strftime('%Y-%m-%d %H:%M:%S') if item.updated_date else None
                } for item in data_query]

                return {"status": "success", "data": serialized_data}
            else:
                return {"status": "error", "message": "No se encontraron cuentas bancarias para el RUT especificado."}

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": f"Error: {error_message}"}

    def store(self, bank_account_user_inputs, session_id, session_rut):
        try:
            bank_account_user = BankAccountUserModel()
            
            # Asignar los valores del formulario a la instancia del modelo
            bank_account_user.user_id = session_id  # Nuevo campo id
            bank_account_user.rut = session_rut
            bank_account_user.bank_account_name = bank_account_user_inputs.bank_account_name
            bank_account_user.bank_account_type_id = bank_account_user_inputs.bank_account_type_id
            bank_account_user.bank_account_number = bank_account_user_inputs.bank_account_number
            bank_account_user.bank_account_email = bank_account_user_inputs.bank_account_email
            bank_account_user.added_date = datetime.now()
            bank_account_user.updated_date = datetime.now()

            self.db.add(bank_account_user)
            
            try:
                self.db.commit()
                return {"status": "success", "message": "Bank Account User saved successfully"}
            except Exception as e:
                self.db.rollback()
                return {"status": "error", "message": f"Error: {str(e)}"}
        
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}

    def update(self, id, bank_account_user_inputs, session_id, session_rut):
        try:
            bank_account_user = self.db.query(BankAccountUserModel).filter(BankAccountUserModel.id == id).first()
            
            if not bank_account_user:
                return {"status": "error", "message": "Bank Account User not found"}

            # Actualizar campos
            bank_account_user.user_id = session_id
            bank_account_user.rut = session_rut
            bank_account_user.bank_account_name = bank_account_user_inputs.bank_account_name
            bank_account_user.bank_account_type_id = bank_account_user_inputs.bank_account_type_id
            bank_account_user.bank_account_number = bank_account_user_inputs.bank_account_number
            bank_account_user.bank_account_email = bank_account_user_inputs.bank_account_email
            bank_account_user.updated_date = datetime.now()

            try:
                self.db.commit()
                return {"status": "success", "message": "Bank Account User updated successfully"}
            except Exception as e:
                self.db.rollback()
                return {"status": "error", "message": f"Error: {str(e)}"}
            
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}

    def delete(self, id):
        try:
            bank_account_user = self.db.query(BankAccountUserModel).filter(BankAccountUserModel.id == id).first()
            
            if not bank_account_user:
                return {"status": "error", "message": "Bank Account User not found"}

            self.db.delete(bank_account_user)
            
            try:
                self.db.commit()
                return {"status": "success", "message": "Bank Account User deleted successfully"}
            except Exception as e:
                self.db.rollback()
                return {"status": "error", "message": f"Error: {str(e)}"}
            
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
