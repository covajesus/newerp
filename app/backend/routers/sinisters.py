from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from app.backend.db.database import get_db
from app.backend.classes.sinister_class import SinisterClass
from app.backend.classes.file_class import FileClass
from app.backend.schemas import SinisterList, Sinister
from sqlalchemy.orm import Session
from datetime import datetime
import base64
import json
import uuid

sinisters = APIRouter(
    prefix="/sinisters",
    tags=["Sinisters"]
)

@sinisters.post("/")
def index(dte: SinisterList, db: Session = Depends(get_db)):
    setting_data = SinisterClass(db).get_all(dte.branch_office_id, dte.page)

    return {"message": setting_data}

@sinisters.post("/store")
def store(
    form_data: Sinister = Depends(Sinister.as_form),
    support: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
        file_category_name = 'sinister'
        unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

        remote_path = f"{file_category_name}_{unique_filename}"
        message = FileClass(db).upload(support, remote_path)
        SinisterClass(db).store(form_data, remote_path)

        return {"message": message}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")
    
@sinisters.delete("/delete/{id}")
def delete(id:int, db: Session = Depends(get_db)):
    sinister_data = SinisterClass(db).get(id)

    sinister_data = json.loads(sinister_data)

    file_name = sinister_data["sinister_data"]["support"]

    # Ruta remota del archivo
    remote_path = f"{file_name}"

    # Eliminar el archivo desde Azure File Share
    message = FileClass(db).delete(remote_path)

    if message == "success":
        # Eliminar el contrato de la base de datos
        SinisterClass(db).delete(id)

    return {"message": message}

@sinisters.get("/download/{id}")
def download(id: int, db: Session = Depends(get_db)):
    sinister_data = SinisterClass(db).get(id)

    sinister_data = json.loads(sinister_data)
    file_name = sinister_data["sinister_data"]["support"]

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
    
@sinisters.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    try:
        # Obtener los datos del contrato
        patent_data = SinisterClass(db).get(id)
        
        # Verificar si se encontró el contrato
        if not patent_data:
            raise HTTPException(status_code=404, detail="Siniestro no encontrada")

        # Si el contrato se encuentra, devolver los datos
        return {"message": patent_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el iva: {str(e)}")

