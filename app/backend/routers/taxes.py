from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.file_class import FileClass
from app.backend.classes.tax_class import TaxClass
from app.backend.schemas import Tax
from app.backend.schemas import TaxList
from datetime import datetime
import uuid


taxes = APIRouter(
    prefix="/taxes",
    tags=["taxes"]
)

@taxes.post("/")
def index(tax: TaxList, db: Session = Depends(get_db)):
    data = TaxClass(db).get_all(tax.month, tax.year, tax.page)

    return {"message": data}


@taxes.post("/store")
def store(
    form_data: Tax = Depends(Tax.as_form),
    support: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # Procesar los datos del formulario
        TaxClass(db).store(form_data, support)

        # Generar un nombre único para el archivo
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]  # 8 caracteres únicos
        file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
        unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

        # Ruta remota en Azure
        remote_path = f"{unique_filename}"  # Organizar archivos en una carpeta específica

        # Subir el archivo a Azure File Share
        message = FileClass(db).upload(support, remote_path)

        return {"message": message}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")
