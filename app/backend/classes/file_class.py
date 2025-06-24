import os
from fastapi import HTTPException, UploadFile

class FileClass:
    def __init__(self, db):
        self.db = db
        self.files_dir = "/var/www/intrajisbackend.com/public_html/files"
        self.base_url = "https://intrajisbackend.com/files"
        # self.files_dir = "C:/Users/jesus/OneDrive/Desktop/escritorio/newerp/files"
        # self.base_url = "http://127.0.0.1:8000/files"

    def upload(self, file: UploadFile, remote_path: str) -> str:
        try:
            full_path = os.path.join(self.files_dir, remote_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(file.file.read())
            return f"Archivo subido exitosamente a {remote_path}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")

    def temporal_upload(self, file_content: bytes, remote_path: str) -> str:
        try:
            full_path = os.path.join(self.files_dir, remote_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(file_content)
            return f"Archivo subido exitosamente a {remote_path}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")

    def delete(self, remote_path: str) -> str:
        try:
            full_path = os.path.join(self.files_dir, remote_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return "success"
            else:
                raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {remote_path}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al eliminar archivo: {str(e)}")

    def download(self, remote_path: str) -> bytes:
        try:
            full_path = os.path.join(self.files_dir, remote_path)
            if os.path.exists(full_path):
                with open(full_path, "rb") as f:
                    return f.read()
            else:
                raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {remote_path}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al descargar archivo: {str(e)}")

    def get(self, remote_path: str) -> str:
        try:
            return f"{self.base_url}/{remote_path}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al generar URL del archivo: {str(e)}")