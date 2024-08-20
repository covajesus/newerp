from app.backend.db.models import UserModel, EmployeeModel
from app.backend.auth.auth_user import generate_bcrypt_hash
from datetime import datetime
from app.backend.classes.helper_class import HelperClass
from werkzeug.security import generate_password_hash

class UserClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(UserModel).order_by(UserModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(UserModel).filter(getattr(UserModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        

    def get_supervisor(self):
        try:
            data = self.db.query(UserModel).order_by(UserModel.nickname).filter(UserModel.rol_id == 3).all()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"  
    
    def store(self, user_inputs):
        numeric_rut = HelperClass().numeric_rut(user_inputs['rut'])
        nickname = HelperClass().nickname(user_inputs['names'], user_inputs['father_lastname'])

        user = UserModel()
        user.rut = numeric_rut
        user.rol_id = 1
        user.clock_rol_id = user_inputs['clock_rol_id']
        user.status_id = 1
        user.visual_rut = user_inputs['rut']
        user.nickname = nickname
        user.hashed_password = generate_bcrypt_hash(user_inputs['password'])
        user.disabled = 0
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
            data = self.db.query(UserModel).filter(UserModel.rut == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
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

    def update(self, id, user_inputs):
        user = self.db.query(UserModel).filter(UserModel.rut == id).first()

        if 'rut' in user_inputs and user_inputs['rut'] is not None:
            numeric_rut = HelperClass().numeric_rut(user_inputs['rut'])
            user.rut = numeric_rut

        if 'rol_id' in user_inputs and user_inputs['rol_id'] is not None:
            user.rol_id = user_inputs['rol_id']

        if 'clock_rol_id' in user_inputs and user_inputs['clock_rol_id'] is not None:
            user.clock_rol_id = user_inputs['clock_rol_id']
        
        if 'status_id' in user_inputs and user_inputs['status_id'] is not None:
            user.status_id = user_inputs['status_id']

        if 'rut' in user_inputs and user_inputs['rut'] is not None:
            user.visual_rut = user_inputs['rut']

        if 'names' in user_inputs and user_inputs['names'] is not None and 'father_lastname' in user_inputs and user_inputs['father_lastname'] is not None:
            nickname = HelperClass().nickname(user_inputs['names'], user_inputs['father_lastname'])
            user.nickname = nickname

        if 'password' in user_inputs and user_inputs['password'] is not None:
            user.hashed_password = generate_bcrypt_hash(user_inputs['password'])
        
        if 'disabled' in user_inputs and user_inputs['disabled'] is not None:
            user.disabled = user_inputs['disabled']

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