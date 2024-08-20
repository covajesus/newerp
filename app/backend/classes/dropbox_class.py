import dropbox
from PIL import Image
from dropbox.exceptions import AuthError, ApiError
from app.backend.classes.setting_class import SettingClass
from app.backend.classes.helper_class import HelperClass
from flask_login import current_user
from datetime import datetime
import os
from pathlib import Path
import base64

class DropboxClass():
    def __init__(self, db):
        self.db = db

    # Función para subir archivos a Dropbox 
    def upload(self, name='', description='', data=None, dropbox_path='', computer_path='', resize=0):
        settings = SettingClass(self.db).get()
        f = data.file

        extension = os.path.splitext(data.filename)[1]

        dropbox_file_name = HelperClass().file_name(str(name), str(description))

        dropbox_path = str(dropbox_path) + str(dropbox_file_name) + str(extension)
        computer_path = str(computer_path) + "/" + str(dropbox_file_name) + str(extension)

        if resize == 1:
            image = Image.open(f)
            image = image.resize((200, 200))
            image.save(os.path.join(computer_path))
        else:
            with open(os.path.join(computer_path), 'wb') as file:
                file.write(f.read())

        dbx = dropbox.Dropbox(settings.dropbox_token)
        with open(os.path.join(computer_path), "rb") as file_data:
            dbx.files_upload(file_data.read(), dropbox_path)

        return str(dropbox_file_name) + str(extension)
        
    def upload_signed_files(self, pdf_bytes, file_path):
        settings = SettingClass.get()
        file_path = '/business_hours/horario.pdf'
        dbx = dropbox.Dropbox(settings.dropbox_token)
        dbx.files_upload(pdf_bytes, file_path, mode=dropbox.files.WriteMode.overwrite)

        return 1

    def upload_local_cloud(self, name = '', description = '', data = '', dropbox_path = '', computer_path = '', resize = 0):
        settings = SettingClass.get()

        f = data['file']

        extesion = os.path.splitext(f.filename)[1]
        dropbox_file_name = str(name) + "_" + str(description)
        now = datetime.now()
        formatted_date = now.strftime("%Y_%m_%d_%H_%M_%S")
        dropbox_file_name = dropbox_file_name + "_" + str(formatted_date) + extesion

        if resize  == 1:
            image = Image.open(f)
            image = image.resize((200, 200))
            image.save(os.path.join(f.filename))
        else:
            f.save(os.path.join(computer_path + dropbox_file_name))

        dropbox_path = dropbox_path + dropbox_file_name
        computer_path = computer_path + dropbox_file_name

        dbx = dropbox.Dropbox(settings.dropbox_token)
        if dbx.files_upload(open(os.path.join(computer_path), "rb").read(), dropbox_path):
            return dropbox_file_name
        else:
            return 0

    def born_document(self, name = '', description = '', data = '', dropbox_path = '', computer_path = '', resize = 0):
        settings = SettingClass.get()

        f = data['file']
        extesion = os.path.splitext(f.filename)[1]
        dropbox_file_name = HelperClass().file_name(str(name), str(description))

        dropbox_path = dropbox_path + dropbox_file_name + extesion
        computer_path = computer_path + dropbox_file_name + extesion
        dropbox_file_name = dropbox_file_name + extesion
        f.save(os.path.join(computer_path))

        dbx = dropbox.Dropbox(settings.dropbox_token)
        if dbx.files_upload(open(os.path.join(computer_path), "rb").read(), dropbox_path):
            return dropbox_file_name
        else:
            return 0

    # Sube la  imagen de la firma del empleado  a Dropbox
    def sign(self, name='', description='', data='', dropbox_path='', computer_path=''):
        settings = SettingClass(self.db).get()

        # Decodifica la imagen desde base64
        signature_bytes = base64.b64decode(data.split(',')[1])
            
        # Directorio donde se guardará la imagen
        upload_dir = "pre_upload_images"
            
        # Asegúrate de que el directorio exista
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            
        # Nombre del archivo
        file_name = f"{name}_signature.jpg"
            
        # Ruta completa del archivo
        file_path = os.path.join(upload_dir, file_name)
            
        # Guarda la imagen en el servidor
        with open(file_path, "wb") as f:
            f.write(signature_bytes)

        dropbox_path = dropbox_path + file_name
        computer_path = computer_path + '\\' + file_name

        dbx = dropbox.Dropbox(settings.dropbox_token)

        # Subir el archivo a Dropbox
        try:
            with open(computer_path, "rb") as f:
                dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode('overwrite'))
            return file_name
        except Exception as e:
            print(f"Error al subir el archivo a Dropbox: {str(e)}")
            return 0

    # Sube la firma del empleado a Dropbox
    def signature(self, file = ''):
        settings = SettingClass.get()

        dbx = dropbox.Dropbox(settings.dropbox_token)
        file_name = '/signature/'+ str(current_user.rut) +'.png'
 
        with open(os.path.join( 'app/static/dist/files/signature_data/' + str(current_user.rut) +'.png'), "wb") as f:
            f.write(file)

        if dbx.files_upload(file, file_name, mode=dropbox.files.WriteMode('overwrite')):
            return  str(current_user.rut) +'.png'
        else:
            return 0

    # Funcion para Obtener la extension del archivo
    def get_file_extension(file_name):
        return Path(file_name).suffix

    def get(self, url, file):
        settings = SettingClass(self.db).get()

        dbx = dropbox.Dropbox(settings.dropbox_token)

        try:
            exist = self.exist(url, file)

            if exist == 1:
                dbx.files_get_metadata(url + file)
            
                link = dbx.files_get_temporary_link(url + file)

                return link.link
            else:
                return 0
        except ApiError:
            return 0
    # Funcion para descargar archivos de Dropbox
    def download(self, url, file):
        settings = SettingClass(self.db).get()

        dbx = dropbox.Dropbox(settings.dropbox_token)

        try:
            file_metadata, file_binary = dbx.files_download(url + file)
            return file_binary
            
        except ApiError as err:
            if err.user_message_text:
                print(err.user_message_text)
            else:
                print(err)
            return 'Error al descargar archivo', 400, None

    # Funcion para eliminar archivos de Dropbox
    def delete(self, url, file):
        settings = SettingClass(self.db).get()

        dbx = dropbox.Dropbox(settings.dropbox_token)

        try:
            dbx.files_get_metadata(url + file)
            
            dbx.files_delete(url + file)

            return 1
        except ApiError:
            return 0
    
    # Funcion para verificar si un archivo existe en Dropbox
    def exist(self, url, file):
        if file == None:
            return 0
        else:
            settings = SettingClass(self.db).get()

            dbx = dropbox.Dropbox(settings.dropbox_token)

            try:
                dbx.files_get_metadata(url + file)
                
                return 1
            except dropbox.exceptions.ApiError as e:
                return str(e)
        

        