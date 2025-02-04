from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.file_class import FileClass
from app.backend.classes.deposit_class import DepositClass
from app.backend.schemas import Deposit
from app.backend.schemas import DepositList
from fastapi import UploadFile, File, HTTPException
from datetime import datetime
import uuid
import json
import base64

deposits = APIRouter(
    prefix="/deposits",
    tags=["Deposits"]
)

@deposits.post("/")
def index(deposit: DepositList, db: Session = Depends(get_db)):
    data = DepositClass(db).get_all(deposit.branch_office_id, deposit.since, deposit.until, deposit.status_id, deposit.page)

    return {"message": data}

@deposits.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    try:
        # Obtener los datos del contrato
        deposit_data = DepositClass(db).get(id)
        
        # Verificar si se encontró el contrato
        if not deposit_data:
            raise HTTPException(status_code=404, detail="Depósito no encontrada")

        # Si el contrato se encuentra, devolver los datos
        return {"message": deposit_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el iva: {str(e)}")

@deposits.get("/support/{id}")
def support(id: int, db: Session = Depends(get_db)):

    deposit = DepositClass(db).get(id)

    deposit_data = json.loads(deposit)
    print(deposit_data["deposit_data"]["support"])
    remote_path = deposit_data["deposit_data"]["support"]

    file = FileClass(db).get(remote_path)

    return {"message": file}

@deposits.post("/store")
def store(
    form_data: Deposit = Depends(Deposit.as_form),
    support: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        # Generar un nombre único para el archivo
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]  # 8 caracteres únicos
        file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
        unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

        # Ruta remota en Azure
        remote_path = f"{unique_filename}"  # Organizar archivos en una carpeta específica

        # Subir el archivo a Azure File Share
        message = FileClass(db).upload(support, remote_path)

        # Procesar los datos del formulario
        DepositClass(db).store(form_data, remote_path)

        return {"message": message}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")
    
@deposits.get("/accept/{id}")
def accept(id:int, db: Session = Depends(get_db)):
    data = DepositClass(db).accept(id)

    return {"message": data}

@deposits.get("/reject/{id}")
def accept(id:int, db: Session = Depends(get_db)):
    data = DepositClass(db).reject(id)

    return {"message": data}