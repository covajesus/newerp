from app.backend.db.models import SliderModel
from datetime import datetime
from sqlalchemy import func
from app.backend.classes.helper_class import HelperClass
from app.backend.classes.dropbox_class import DropboxClass
import os
import json
import requests

class SliderClass:
    def __init__(self, db):
        self.db = db

       
    def upload_image(self, file):
        slider = SliderModel()
        slider.support = file
        slider.added_date = datetime.now()
        slider.updated_date = datetime.now()

        self.db.add(slider)
        self.db.commit()
        
        return 1
    
    def delete(self, id):
        data = self.db.query(SliderModel).filter(SliderModel.id == id ).first()
        support = data.support
        self.db.delete(data)
        self.db.commit()
        
        return support
    
    def get(self):
        data = self.db.query(SliderModel).all()
        return data
    
    def get_resources(self, external_token, rut, password):
        """
        Obtiene recursos desde la API externa de sliders
        """
        from app.backend.classes.authentication_class import AuthenticationClass
        
        try:
            url = "https://api.jisreportes.com/resources/?limit=40"
            
            # Primero intentar con el token actual
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {external_token}"
            }
            
            response = requests.get(
                url,
                headers=headers
            )
            
            # Si el token está vencido (401) o el mensaje contiene "token-invalido", crear uno nuevo
            if response.status_code == 401 or "token-invalido" in response.text.lower():
                fresh_token = AuthenticationClass(self.db).create_external_token(rut, password)
                headers["Authorization"] = f"Bearer {fresh_token}"
                response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Procesar los datos para agregar el prefijo a path_imagen
                for item in data:
                    if 'path_imagen' in item and item['path_imagen']:
                        # Si path_imagen comienza con /static, agregar el prefijo
                        if item['path_imagen'].startswith('/static'):
                            item['path_imagen'] = f"https://api.jisreportes.com{item['path_imagen']}"
                
                return data
            else:
                return {
                    "error": f"Error en la petición: {response.status_code}",
                    "message": response.text
                }
                
        except Exception as e:
            error_message = str(e)
            return {"error": f"Error: {error_message}"}