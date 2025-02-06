from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.file_class import FileClass
from app.backend.classes.tax_class import TaxClass
from app.backend.schemas import Tax
from app.backend.schemas import TaxList
from datetime import datetime
import uuid
import json
import base64

taxes = APIRouter(
    prefix="/taxes",
    tags=["Taxes"]
)

@taxes.post("/")
def index(tax: TaxList, db: Session = Depends(get_db)):
    data = TaxClass(db).get_all(tax.period, tax.page)

    return {"message": data}

@taxes.post("/store")
def store(
    form_data: Tax = Depends(Tax.as_form),
    support: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        # Generar un nombre único para el archivo
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]  # 8 caracteres únicos
        file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
        file_category_name = 'tax'
        unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

        # Ruta remota en Azure
        remote_path = f"{file_category_name}_{unique_filename}"  # Organizar archivos en una carpeta específica

        # Subir el archivo a Azure File Share
        message = FileClass(db).upload(support, remote_path)

        # Procesar los datos del formulario
        TaxClass(db).store(form_data, remote_path)

        return {"message": message}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")

@taxes.get("/tax/{tax_id}")
def download(tax_id:int, db: Session = Depends(get_db)):
    data = TaxClass(db).download(tax_id)

    return {"message": data}

@taxes.delete("/delete/{id}")
def delete(id:int, db: Session = Depends(get_db)):
    tax_data = TaxClass(db).get(id)

    tax_data = json.loads(tax_data)

    file_name = tax_data["tax_data"]["support"]

    # Ruta remota del archivo
    remote_path = f"{file_name}"

    # Eliminar el archivo desde Azure File Share
    message = FileClass(db).delete(remote_path)

    if message == "success":
        # Eliminar el contrato de la base de datos
        TaxClass(db).delete(id)

    return {"message": message}

@taxes.get("/download/{id}")
def download(id: int, db: Session = Depends(get_db)):
    # Obtener los datos del contrato
    tax_data = TaxClass(db).get(id)

    tax_data = json.loads(tax_data)
    file_name = tax_data["tax_data"]["support"]
    print(file_name)

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
    
@taxes.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    try:
        # Obtener los datos del contrato
        tax_data = TaxClass(db).get(id)
        
        # Verificar si se encontró el contrato
        if not tax_data:
            raise HTTPException(status_code=404, detail="Contrato no encontrado")

        # Si el contrato se encuentra, devolver los datos
        return {"message": tax_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el iva: {str(e)}")

@taxes.put("/update/{id}")
def update(
    id: int,
    form_data: Tax = Depends(Tax.as_form),
    support: UploadFile = File(None),  # El archivo es opcional en la actualización
    db: Session = Depends(get_db)
):
    try:
        # Verificar si el contrato existe
        tax_data = TaxClass(db).get(id)
        if not tax_data:
            raise HTTPException(status_code=404, detail="Iva no encontrado")

        tax_data = json.loads(tax_data)

        # Nombre del archivo previo
        previous_file_name = tax_data["tax_data"]["support"]
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
        TaxClass(db).update(id, form_data, new_file_name)

        return {"message": "Iva actualizado exitosamente"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar el iva: {str(e)}")
