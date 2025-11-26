from fastapi import APIRouter, Depends, Form
from typing import List
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.file_class import FileClass
from app.backend.classes.maintenance_class import MaintenanceClass
from app.backend.schemas import MaintenanceList
from fastapi import UploadFile, File, HTTPException
from datetime import datetime
from app.backend.auth.auth_user import get_current_active_user
from app.backend.schemas import UserLogin
import uuid
import json
import base64

maintenances = APIRouter(
    prefix="/maintenances",
    tags=["Maintenances"]
)

@maintenances.post("/")
def index(maintenance: MaintenanceList, db: Session = Depends(get_db)):
    data = MaintenanceClass(db).get_all(maintenance.branch_office_id, maintenance.page)

    return {"message": data}

@maintenances.post("/store")
def store(
    branch_office_id: int = Form(...),
    maintenance_date: str = Form(...),
    files: List[UploadFile] = File(None),  # ahora opcional
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    maintenance_id = MaintenanceClass(db).store(branch_office_id, maintenance_date)

    for i in range(len(files)):
        # Manejo del archivo
        support = files[i] if files and i < len(files) else None
        remote_path = None

        if support and support.filename != "empty-file.jpg":
            timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            unique_id = uuid.uuid4().hex[:8]
            file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
            file_category_name = 'maintenance'
            unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"
            remote_path = f"{file_category_name}_{unique_filename}"

            FileClass(db).upload(support, remote_path)

        # Guardar respuesta
        MaintenanceClass(db).store_datum(
            maintenance_id,
            i + 1,
            remote_path
        )

    return {"message": "Mantenimiento creado con éxito", "maintenance_id": maintenance_id}

@maintenances.delete("/delete/{id}")
def delete(id: int, db: Session = Depends(get_db)):
    maintenance_data = MaintenanceClass(db).get_all_details(id)
    maintenance_data = json.loads(maintenance_data)

    supports = [
        item["support"]
        for item in maintenance_data.get("maintenance_data", [])
        if item.get("support")
    ]

    # Eliminar todos los archivos de soporte
    for support_file in supports:
        remote_path = f"{support_file}"
        FileClass(db).delete(remote_path)

    # Eliminar los registros en base de datos
    MaintenanceClass(db).delete(id)
    MaintenanceClass(db).delete_datum(id)

    return {"message": "success"}

@maintenances.get("/maintenance_data/{id}/{maintenance_id}")
def maintenance_data(id: int, maintenance_id: int, db: Session = Depends(get_db)):
    message = MaintenanceClass(db).get_files(id, maintenance_id)

    return message

@maintenances.get("/download/{id}")
def download(id: int, db: Session = Depends(get_db)):
    # Obtener los datos del contrato

    maintenance_data = MaintenanceClass(db).get(id)

    maintenance_data = json.loads(maintenance_data)
    file_name = maintenance_data["maintenance_data"]["support"]

    # Ruta remota del archivo
    remote_path = f"{file_name}"

    # Descargar archivo desde Azure File Share
    file_contents = FileClass(db).download(remote_path)

    # Convertir el contenido del archivo a base64
    encoded_file = base64.b64encode(file_contents).decode('utf-8')

    # Retornar el nombre del archivo y su contenido como base64
    return {
        "file_name": file_name,
        "file_data": encoded_file
    }

@maintenances.get("/support/{support}")
def get_support(support: str, db: Session = Depends(get_db)):
    remote_path = support

    file = FileClass(db).get(remote_path)

    return {"message": file}
    
@maintenances.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    try:
        # Obtener los datos del contrato
        maintenance_data = MaintenanceClass(db).get(id)
        
        # Verificar si se encontró el contrato
        if not maintenance_data:
            raise HTTPException(status_code=404, detail="Mantenimiento no encontrado")

        # Si el contrato se encuentra, devolver los datos
        return {"message": maintenance_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el iva: {str(e)}")