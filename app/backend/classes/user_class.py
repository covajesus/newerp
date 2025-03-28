import json
from app.backend.db.models import UserModel, EmployeeModel
from app.backend.auth.auth_user import generate_bcrypt_hash
from datetime import datetime
from app.backend.classes.helper_class import HelperClass
from werkzeug.security import generate_password_hash

class UserClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, rut=None, page=0, items_per_page=10):
        try:
            filters = []
            if rut is not None:
                filters.append(UserModel.rut == rut)

            query = self.db.query(
                UserModel.id, 
                UserModel.rut, 
                UserModel.full_name, 
                UserModel.rol_id, 
                UserModel.email,
                UserModel.phone,
                UserModel.added_date
            ).filter(
                *filters
            ).order_by(
                UserModel.rut
            )

            if page > 0:
                total_items = query.count()
                total_pages = (total_items + items_per_page - 1)

                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                serialized_data = [{
                    "id": user.id,
                    "rut": user.rut,
                    "full_name": user.full_name,
                    "rol_id": user.rol_id,
                    "email": user.email,
                    "phone": user.phone,
                    "added_date": user.added_date
                } for user in data]

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }

            else:
                data = query.all()

                serialized_data = [{
                    "id": user.id,
                    "rut": user.rut,
                    "full_name": user.full_name,
                    "rol_id": user.rol_id,
                    "email": user.email,
                    "phone": user.phone,
                    "added_date": user.added_date
                } for user in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
    
    def get(self, field, value):
        try:
            data_query = self.db.query(UserModel).filter(getattr(UserModel, field) == value).first()

            if data_query:
                user_data = {
                    "id": data_query.id,
                    "rut": data_query.rut,
                    "full_name": data_query.full_name,
                    "rol_id": data_query.rol_id,
                    "email": data_query.email,
                    "phone": data_query.phone,
                    "hashed_password": data_query.hashed_password,
                    "added_date": data_query.added_date
                }

                result = {
                    "user_data": user_data
                }

                serialized_result = json.dumps(result)

                return serialized_result

            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get_supervisors(self):
        try:
            data = self.db.query(UserModel).order_by(UserModel.nickname).filter(UserModel.rol_id == 3).all()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"  
    
    def store(self, user_inputs):
        user = UserModel()
        user.rut = user_inputs['rut']
        user.rol_id = user_inputs['rol_id']
        user.branch_office_id = user_inputs['branch_office_id']
        user.full_name = user_inputs['full_name']
        user.hashed_password = generate_bcrypt_hash(user_inputs['password'])
        user.email = user_inputs['email']
        user.phone = user_inputs['phone']
        user.added_date = datetime.now()
        user.updated_date = datetime.now()

        self.db.add(user)
        try:
            self.db.commit()

            return 1
        except Exception as e:
            return 0
        
    def delete(self, id):
        try:
            data = self.db.query(UserModel).filter(UserModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 'success'
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def refresh_password(self, rut):
        user = self.db.query(UserModel).filter(UserModel.rut == rut).first()
        user.password = 'pbkdf2:sha256:260000$9199IIO4oyzykgL2$721b8c61330f838acd950f8104f364efc05d513efec2c829fcd773ef4402f10e'
        user.hashed_password = 'pbkdf2:sha256:260000$9199IIO4oyzykgL2$721b8c61330f838acd950f8104f364efc05d513efec2c829fcd773ef4402f10e'
        user.status_id = 1
        user.updated_date = datetime.now()
        self.db.add(user)
        
        try:
            self.db.commit()

            return 1
        except Exception as e:
            return 0

    def update(self, id, form_data):
        user = self.db.query(UserModel).filter(UserModel.id == id).first()

        user.rol_id = form_data['rol_id']
        user.rut = form_data['rut']
        user.full_name = form_data['full_name']
        user.email = form_data['email']
        user.phone = form_data['phone']

        user.updated_date = datetime.now()

        self.db.add(user)

        try:
            self.db.commit()

            return 1
        except Exception as e:
            return 0

    def confirm_email(self, user_inputs):
        print(user_inputs.visual_rut)
        user = self.db.query(UserModel).filter(UserModel.visual_rut == user_inputs.visual_rut).first()
        employee = self.db.query(EmployeeModel).filter(EmployeeModel.visual_rut == user_inputs.visual_rut).first()

        print(user)  # Print user after query
        print(employee)  # Print employee after query

        if not user or not employee:
            return 0  # Return 0 if no user or employee is found

        employee.personal_email = user_inputs.personal_email
        user.status_id = 1
        user.updated_date = datetime.now()
        employee.updated_date = datetime.now()

        self.db.add(user)
        self.db.add(employee)  # Add the updated employee to the database session

        try:
            self.db.commit()
            return 1
        except Exception as e:
            self.db.rollback()  # Rollback the session in case of error
            print(e)  # Print the exception
            return 0