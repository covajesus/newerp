# Updated: 2024 - Fixed create_external_token error handling
from app.backend.db.models import UserModel, EmployeeModel
from fastapi import HTTPException
from app.backend.auth.auth_user import pwd_context
from app.backend.classes.setting_class import SettingClass
from app.backend.classes.user_class import UserClass
from datetime import datetime, timedelta
from typing import Union
import os
from jose import jwt
import requests
import json
import bcrypt

class AuthenticationClass:
    def __init__(self, db):
        self.db = db

    def authenticate_user(self, rut, password):
        user = UserClass(self.db).get('rut', rut)
        
        # Verificar si user es None o un mensaje de error
        if not user or user == "No se encontraron datos para el campo especificado." or (isinstance(user, str) and user.startswith("Error:")):
            # No exponer detalles específicos del error por seguridad
            raise HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
        
        # Intentar parsear el JSON
        try:
            response_data = json.loads(user)
        except json.JSONDecodeError:
            # No exponer detalles del error de parsing por seguridad
            raise HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})

        if not self.verify_password(password, response_data["user_data"]["hashed_password"]):
            raise HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
        return response_data
        
    def verify_password(self, plain_password, hashed_password):
        # Use bcrypt directly instead of passlib (compatibility issue with Python 3.13)
        try:
            # Verificar que hashed_password no esté vacío
            if not hashed_password:
                return False
            
            # Verificar formato del hash bcrypt (debe empezar con $2a$, $2b$, o $2y$)
            if isinstance(hashed_password, str) and not hashed_password.startswith(('$2a$', '$2b$', '$2y$')):
                return False
            
            # Asegurarse de que plain_password esté en bytes
            plain_password_bytes = plain_password.encode('utf-8') if isinstance(plain_password, str) else plain_password
            
            # Asegurarse de que hashed_password esté en bytes
            # Si ya es bytes, usarlo directamente; si es string, convertirlo
            if isinstance(hashed_password, str):
                hashed_password_bytes = hashed_password.encode('utf-8')
            else:
                hashed_password_bytes = hashed_password
            
            result = bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
            return result
        except Exception:
            # No exponer detalles del error por seguridad
            return False
    
    def create_external_token(self, rut, password):
        url = "https://api.jisreportes.com/login"
        data = {
            "rut": rut,
            "password": password
        }

        try:
            response = requests.post(url, json=data, timeout=10)
            
            # Verificar si la respuesta es exitosa
            if response.status_code != 200:
                # No exponer detalles de la respuesta de error por seguridad
                return None
            
            # Intentar parsear JSON
            try:
                json_data = response.json()
                token = json_data.get("access_token")
                return token
            except json.JSONDecodeError:
                # No exponer detalles del error de parsing por seguridad
                return None
                
        except requests.exceptions.RequestException:
            # No exponer detalles del error de conexión por seguridad
            return None
    
    def create_token(self, data: dict, time_expire: Union[datetime, None] = None):
        data_copy = data.copy()
        if time_expire is None:
            expires = datetime.utcnow() + timedelta(minutes=1000000)
        else:
            expires = datetime.utcnow() + time_expire

        data_copy.update({"exp": expires})
        token = jwt.encode(data_copy, os.environ['SECRET_KEY'], algorithm=os.environ['ALGORITHM'])

        return token
    
    def forgot(self, data):
        try:
            query = self.db.query(EmployeeModel).filter(EmployeeModel.personal_email == data.email).first()
            if not query:
                return 0
            else:
                print(query.names)
                return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}" 

    def update_password(self, phone: str, new_password: str):
        # Buscar el usuario por su número de documento
        existing_user = self.db.query(UserModel).filter(UserModel.phone == phone).one_or_none()

        if not existing_user:
            return "No data found"

        # Hashear la nueva contraseña
        hashed_password = self.generate_bcrypt_hash(new_password)

        # Actualizar el campo en el modelo
        existing_user.hashed_password = hashed_password.decode('utf-8')  # Asegurarse de guardar como string

        # Confirmar los cambios
        self.db.commit()

        return 1

    def generate_bcrypt_hash(self, input_string):
        encoded_string = input_string.encode('utf-8')

        salt = bcrypt.gensalt()

        hashed_string = bcrypt.hashpw(encoded_string, salt)

        return hashed_string

    def create_simplefactura_token(self):
        url = "https://api.simplefactura.cl/token"

        headers = {
            'Content-Type': 'application/json'
        }

        payload = {
            "email": "jesuscova@jisparking.com",
            "password": "Jgames88!"
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            data = response.json()
            access_token = data.get("accessToken")
            SettingClass(self.db).update_token(access_token)
            return access_token
        else:
            # No exponer detalles del error por seguridad
            return None
            
    def check_simplefactura_token(self):
        setting_data = SettingClass(self.db).get()
        token = setting_data["setting_data"]["simplefactura_token"]
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        url = "https://api.simplefactura.cl/token/expire"

        response = requests.get(url, headers=headers)

        if response.status_code == 401:
            return 0

        if response.status_code == 429:
            return 2

        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            # No exponer detalles de la respuesta por seguridad
            return 3

