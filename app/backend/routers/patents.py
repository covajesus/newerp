from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.file_class import FileClass
from app.backend.classes.patent_class import PatentClass
from app.backend.schemas import Patent
from app.backend.schemas import PatentList
from fastapi import UploadFile, File, HTTPException
from datetime import datetime
import uuid
import json
import base64
from app.backend.auth.auth_user import get_current_active_user
from app.backend.schemas import UserLogin

patents = APIRouter(
    prefix="/patents",
    tags=["Patentents"]
)

@patents.post("/")
def index(patent: PatentList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PatentClass(db).get_all(session_user.rol_id, session_user.rut, patent.branch_office_id, patent.semester, patent.year, patent.page)

    return {"message": data}

@patents.post("/store")
def store(
    form_data: Patent = Depends(Patent.as_form),
    support: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        # Generar un nombre único para el archivo
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]  # 8 caracteres únicos
        file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
        file_category_name = 'patent'
        unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

        # Ruta remota en Azure
        remote_path = f"{file_category_name}_{unique_filename}"  # Organizar archivos en una carpeta específica

        # Subir el archivo a Azure File Share
        message = FileClass(db).upload(support, remote_path)

        # Procesar los datos del formulario
        PatentClass(db).store(form_data, remote_path)

        return {"message": message}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")

@patents.delete("/delete/{id}")
def delete(id:int, db: Session = Depends(get_db)):
    patent_data = PatentClass(db).get(id)

    patent_data = json.loads(patent_data)

    file_name = patent_data["patent_data"]["support"]

    # Ruta remota del archivo
    remote_path = f"{file_name}"

    # Eliminar el archivo desde Azure File Share
    message = FileClass(db).delete(remote_path)

    if message == "success":
        # Eliminar el contrato de la base de datos
        PatentClass(db).delete(id)

    return {"message": message}

@patents.get("/download/{id}")
def download(id: int, db: Session = Depends(get_db)):
    # Obtener los datos del contrato

    patent_data = PatentClass(db).get(id)

    patent_data = json.loads(patent_data)
    file_name = patent_data["patent_data"]["support"]

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
    
@patents.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    try:
        # Obtener los datos del contrato
        patent_data = PatentClass(db).get(id)
        
        # Verificar si se encontró el contrato
        if not patent_data:
            raise HTTPException(status_code=404, detail="Patente no encontrada")

        # Si el contrato se encuentra, devolver los datos
        return {"message": patent_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el iva: {str(e)}")

@patents.put("/update/{id}")
def update(
    id: int,
    form_data: Patent = Depends(Patent.as_form),
    support: UploadFile = File(None),  # El archivo es opcional en la actualización
    db: Session = Depends(get_db)
):
    try:
        # Verificar si el contrato existe
        patent_data = PatentClass(db).get(id)
        if not patent_data:
            raise HTTPException(status_code=404, detail="Iva no encontrado")

        patent_data = json.loads(patent_data)

        # Nombre del archivo previo
        previous_file_name = patent_data["patent_data"]["support"]
        remote_path_previous = f"{previous_file_name}" if previous_file_name else None

        new_file_name = previous_file_name  # Por defecto, mantener el archivo previo
        if support:
            # Si se proporciona un nuevo archivo, generar un nombre único
            timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            unique_id = uuid.uuid4().hex[:8]
            file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
            new_file_name = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"
            remote_path_new = f"{new_file_name}"

            # Subir el nuevo archivo
            FileClass(db).upload(support, remote_path_new)

            # Si había un archivo previo, eliminarlo
            if remote_path_previous:
                FileClass(db).delete(remote_path_previous)

        # Actualizar los datos del contrato en la base de datos
        PatentClass(db).update(id, form_data, new_file_name)

        return {"message": "Patente actualizada exitosamente"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar el iva: {str(e)}")
