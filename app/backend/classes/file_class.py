from azure.storage.fileshare import ShareFileClient
from fastapi import HTTPException
from fastapi import UploadFile
import os

class FileClass:
    def __init__(self, db):
        self.db = db
        self.account_name = os.getenv("ACCOUNT_NAME") # Cambia por tu nombre de cuenta
        self.account_key = os.getenv("AZURE_STORAGE_KEY")  # Cambia por tu clave
        self.share_name = "files" 

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