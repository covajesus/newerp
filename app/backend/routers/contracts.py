from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from datetime import datetime
import uuid
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.file_class import FileClass
from app.backend.classes.contract_class import ContractClass
from app.backend.schemas import Contract
from app.backend.schemas import ContractList


contracts = APIRouter(
    prefix="/contracts",
    tags=["contracts"]
)

@contracts.post("/")
def index(contract: ContractList, db: Session = Depends(get_db)):
    data = ContractClass(db).get_all(contract.branch_office_id, contract.page)

    return {"message": data}


@contracts.post("/store")
def store(
    form_data: Contract = Depends(Contract.as_form),
    support: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # Procesar los datos del contrato
        ContractClass(db).store(form_data, support)

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