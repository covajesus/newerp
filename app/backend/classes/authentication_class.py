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
        response_data = json.loads(user)

        if not user:
            raise HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})

        if not self.verify_password(password, response_data["user_data"]["hashed_password"]):
            raise HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
        return response_data
        
    def verify_password(self, plain_password, hashed_password):
        # Use bcrypt directly instead of passlib (compatibility issue with Python 3.13)
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'), 
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False
    
    def create_external_token(self, rut, password):
        url = "https://api.jisreportes.com/login"
        data = {
            "rut": rut,
            "password": password
        }
        print(data)

        response = requests.post(url, json=data)

        json_data = response.json()
        token = json_data.get("access_token")

        return token
    
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
            print("Access Token:", access_token)
            SettingClass(self.db).update_token(access_token)
            return access_token
        else:
            print("Error al obtener el token:", response.status_code, response.text)
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

        print(f"Status Code: {response.status_code}")

        if response.status_code == 401:
            return 0

        if response.status_code == 429:
            return 2

        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            print("No se pudo decodificar la respuesta JSON.")
            print(response.text)
            return 3

