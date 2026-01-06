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
        
        # Debug: ver qué devuelve user
        print(f"DEBUG - Tipo de user: {type(user)}")
        print(f"DEBUG - Valor de user: {user}")
        print(f"DEBUG - user es None: {user is None}")
        if user:
            print(f"DEBUG - Longitud de user: {len(str(user))}")
            print(f"DEBUG - Primeros 100 caracteres: {str(user)[:100]}")
        
        # Verificar si user es None o un mensaje de error
        if not user or user == "No se encontraron datos para el campo especificado." or (isinstance(user, str) and user.startswith("Error:")):
            print(f"DEBUG - Usuario no encontrado o error: {user}")
            raise HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
        
        # Intentar parsear el JSON
        try:
            response_data = json.loads(user)
        except json.JSONDecodeError as e:
            print(f"DEBUG - Error al parsear JSON: {str(e)}")
            print(f"DEBUG - Contenido que falló: {user}")
            raise HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})

        # Debug: imprimir información útil
        print(f"Verificando contraseña para RUT: {rut}")
        print(f"Tipo de hashed_password: {type(response_data['user_data']['hashed_password'])}")
        print(f"Longitud de hashed_password: {len(response_data['user_data']['hashed_password']) if response_data['user_data']['hashed_password'] else 0}")

        if not self.verify_password(password, response_data["user_data"]["hashed_password"]):
            raise HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
        return response_data
        
    def verify_password(self, plain_password, hashed_password):
        # Use bcrypt directly instead of passlib (compatibility issue with Python 3.13)
        try:
            # Debug: información de la contraseña
            print(f"DEBUG verify_password - Contraseña recibida (longitud): {len(str(plain_password))}")
            print(f"DEBUG verify_password - Hash recibido (primeros 30 chars): {hashed_password[:30] if hashed_password else 'None'}...")
            print(f"DEBUG verify_password - Hash completo (longitud): {len(str(hashed_password)) if hashed_password else 0}")
            
            # Verificar que hashed_password no esté vacío
            if not hashed_password:
                print("Error: hashed_password está vacío")
                return False
            
            # Verificar formato del hash bcrypt (debe empezar con $2a$, $2b$, o $2y$)
            if isinstance(hashed_password, str) and not hashed_password.startswith(('$2a$', '$2b$', '$2y$')):
                print(f"Error: Formato de hash inválido. Hash recibido: {hashed_password[:20]}...")
                return False
            
            # Asegurarse de que plain_password esté en bytes
            plain_password_bytes = plain_password.encode('utf-8') if isinstance(plain_password, str) else plain_password
            
            # Asegurarse de que hashed_password esté en bytes
            # Si ya es bytes, usarlo directamente; si es string, convertirlo
            if isinstance(hashed_password, str):
                hashed_password_bytes = hashed_password.encode('utf-8')
            else:
                hashed_password_bytes = hashed_password
            
            print(f"DEBUG verify_password - Comparando contraseña con hash bcrypt...")
            result = bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
            print(f"Resultado de verificación de contraseña: {result}")
            
            # Si falla, intentar verificar si el hash está correctamente formateado
            if not result:
                print(f"DEBUG verify_password - La verificación falló. Hash completo: {hashed_password}")
                print(f"DEBUG verify_password - ¿El hash tiene 60 caracteres? {len(hashed_password) == 60}")
                print(f"DEBUG verify_password - ¿El hash termina correctamente? {hashed_password[-1] if len(hashed_password) > 0 else 'N/A'}")
            
            return result
        except Exception as e:
            print(f"Error al verificar contraseña: {str(e)}")
            print(f"Tipo de error: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_external_token(self, rut, password):
        url = "https://api.jisreportes.com/login"
        data = {
            "rut": rut,
            "password": password
        }
        print(f"DEBUG - Intentando obtener token externo para RUT: {rut}")

        try:
            response = requests.post(url, json=data, timeout=10)
            
            # Debug: información de la respuesta
            print(f"DEBUG - Status code de API externa: {response.status_code}")
            print(f"DEBUG - Headers de respuesta: {response.headers}")
            print(f"DEBUG - Contenido de respuesta (primeros 200 chars): {response.text[:200]}")
            
            # Verificar si la respuesta es exitosa
            if response.status_code != 200:
                print(f"DEBUG - Error en API externa. Status: {response.status_code}, Text: {response.text}")
                return None
            
            # Intentar parsear JSON
            try:
                json_data = response.json()
                token = json_data.get("access_token")
                print(f"DEBUG - Token externo obtenido: {token is not None}")
                return token
            except json.JSONDecodeError as e:
                print(f"DEBUG - Error al parsear JSON de API externa: {str(e)}")
                print(f"DEBUG - Respuesta completa: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"DEBUG - Error de conexión con API externa: {str(e)}")
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

