from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.file_class import FileClass
from app.backend.classes.demarcation_class import DemarcationClass
from app.backend.schemas import Patent
from app.backend.schemas import DemarcationList, Demarcation
from fastapi import UploadFile, File, HTTPException
from datetime import datetime
import uuid
import json
import os
import base64

demarcations = APIRouter(
    prefix="/demarcations",
    tags=["Demarcations"]
)

@demarcations.post("/")
def index(demarcation: DemarcationList, db: Session = Depends(get_db)):
    data = DemarcationClass(db).get_all(demarcation.page)

    return {"message": data}

@demarcations.post("/store")
def store(
    form_data: Demarcation = Depends(Demarcation.as_form),
    db: Session = Depends(get_db)
):
    i = 1

    for attr_name in dir(form_data):
        if attr_name.startswith("file_"):
            file = getattr(form_data, attr_name)
            if file:
                timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                unique_id = uuid.uuid4().hex[:8]  # 8 caracteres únicos
                file_extension = os.path.splitext(file.filename)[1]
                file_category_name = 'demarcation'
                unique_filename = f"{timestamp}_{unique_id}{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

                if i == 1:
                    remote_path1 = f"{file_category_name}_{unique_filename}"
                    message = FileClass(db).upload(file, remote_path1)
                elif i == 2:
                    remote_path2 = f"{file_category_name}_{unique_filename}"
                    message = FileClass(db).upload(file, remote_path2)
                elif i == 3:
                    remote_path3 = f"{file_category_name}_{unique_filename}"
                    message = FileClass(db).upload(file, remote_path3)
                elif i == 4:
                    remote_path4 = f"{file_category_name}_{unique_filename}"
                    message = FileClass(db).upload(file, remote_path4)
                elif i == 5:
                    remote_path5 = f"{file_category_name}_{unique_filename}"
                    message = FileClass(db).upload(file, remote_path5)
                elif i == 6:
                    remote_path6 = f"{file_category_name}_{unique_filename}"
                    message = FileClass(db).upload(file, remote_path6)

                i += 1

    DemarcationClass(db).store(form_data, remote_path1, remote_path2, remote_path3, remote_path4, remote_path5, remote_path6)

@demarcations.delete("/delete/{id}")
def delete(id:int, db: Session = Depends(get_db)):
    message = DemarcationClass(db).delete(id)

    return {"message": message}
    
@demarcations.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    try:
        # Obtener los datos del contrato
        demarcation_data = DemarcationClass(db).get(id)
        
        # Verificar si se encontró el contrato
        if not demarcation_data:
            raise HTTPException(status_code=404, detail="Demarcación no encontrada")

        # Si el contrato se encuentra, devolver los datos
        return {"message": demarcation_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el iva: {str(e)}")

@demarcations.put("/update/{id}")
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
