from azure.storage.fileshare import ShareFileClient
from azure.storage.fileshare import generate_file_sas, FileSasPermissions
from fastapi import HTTPException, UploadFile
from azure.core.exceptions import ResourceNotFoundError
from fastapi import UploadFile
import os
from datetime import datetime, timedelta

class FileClass:
    def __init__(self, db):
        self.db = db
        self.account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
        self.account_key = os.environ.get("AZURE_STORAGE_ACCOUNT_KEY")
        self.share_name = "files" 
        self.sas = os.environ.get("AZURE_STORAGE_SAS_TOKEN")

    def upload(self, file: UploadFile, remote_path: str) -> str:
        """
        Sube un archivo al Azure File Share.
        """
        try:
            # Crear cliente para el archivo
            file_client = ShareFileClient(
                account_url=f"https://erpjis.file.core.windows.net/",
                share_name=self.share_name,
                file_path=remote_path,
                credential=self.account_key,
            )

            # Leer el contenido del archivo subido
            file_contents = file.file.read()

            # Subir el archivo a Azure File Share
            file_client.upload_file(file_contents)

            # Retornar mensaje de éxito
            return f"Archivo subido exitosamente a {remote_path}"

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")
        
    def temporal_upload(self, file_content, remote_path: str) -> str:
        """
        Sube un archivo al Azure File Share.
        """
        try:
            # Crear cliente para el archivo
            file_client = ShareFileClient(
                account_url=f"https://erpjis.file.core.windows.net/",
                share_name=self.share_name,
                file_path=remote_path,
                credential=self.account_key,
            )

            # Subir el archivo a Azure File Share
            file_client.upload_file(file_content)
            print(file_client)
            # Retornar mensaje de éxito
            return f"Archivo subido exitosamente a {remote_path}"

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)})")
                                
    def delete(self, remote_path: str) -> str:
        """
        Elimina un archivo desde Azure File Share.
        """
        try:
            # Crear cliente para el archivo
            file_client = ShareFileClient(
                account_url=f"https://erpjis.file.core.windows.net/",
                share_name=self.share_name,
                file_path=remote_path,
                credential=self.account_key,
            )

            # Eliminar el archivo
            file_client.delete_file()

            return f"success"

        except ResourceNotFoundError:
            raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {remote_path}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al eliminar archivo: {str(e)}")


    def download(self, remote_path: str) -> bytes:
        """
        Descarga un archivo desde Azure File Share.
        """
        try:
            # Crear cliente para el archivo
            file_client = ShareFileClient(
                account_url=f"https://erpjis.file.core.windows.net/",
                share_name=self.share_name,
                file_path=remote_path,
                credential=self.account_key,
            )

            # Descargar el contenido del archivo
            download_stream = file_client.download_file()

            # Leer el contenido del archivo descargado
            file_contents = download_stream.readall()

            return file_contents

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al descargar archivo: {str(e)}")
    
    def get(self, remote_path: str) -> str:

        try:
            public_url = f"https://{self.account_name}.file.core.windows.net/{self.share_name}/{remote_path}?{self.sas}"

            return public_url

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al descargar archivo: {str(e)}")

