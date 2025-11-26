from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.file_class import FileClass
from app.backend.classes.deposit_class import DepositClass
from app.backend.schemas import Deposit, DepositList
from app.backend.db.models import DepositModel
from fastapi import UploadFile, File, HTTPException
from datetime import datetime
import uuid
from app.backend.auth.auth_user import get_current_active_user
from app.backend.schemas import UserLogin
import json

deposits = APIRouter(
    prefix="/deposits",
    tags=["Deposits"]
)

@deposits.post("/")
def index(deposit: DepositList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = DepositClass(db).get_all(session_user.rol_id, session_user.rut, deposit.branch_office_id, deposit.since, deposit.until, deposit.status_id, deposit.page)

    return {"message": data}

@deposits.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    try:
        deposit_data = DepositClass(db).get(id)
        
        if not deposit_data:
            raise HTTPException(status_code=404, detail="Depósito no encontrada")

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
    # Validar que el depósito no existe (evitar duplicados)
    existing_deposit = db.query(DepositModel).filter(
            DepositModel.branch_office_id == form_data.branch_office_id,
            DepositModel.payment_number == form_data.payment_number,
            DepositModel.deposited_amount == form_data.deposited_amount
        ).count()

        
    if existing_deposit > 0:
        return {
            "status": "error", 
            "message": f"Ya existe un depósito con los mismos datos"
        }
        
    try:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
        file_category_name = 'deposit'
        unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

        remote_path = f"{file_category_name}_{unique_filename}"

        message = FileClass(db).upload(support, remote_path)

        DepositClass(db).store(form_data, remote_path)

        return {"message": message}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")

@deposits.post("/accept/{id}")
def accept(id: int, deposit_data: Deposit, db: Session = Depends(get_db)):
    """
    Acepta un depósito con datos adicionales del frontend
    """
    try:
        # Llamar al método accept con los datos adicionales
        result = DepositClass(db).accept(id, deposit_data)
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al aceptar depósito: {str(e)}")

@deposits.post("/reject/{id}")
def reject(id: int, deposit_data: Deposit, db: Session = Depends(get_db)):
    """
    Rechaza un depósito con datos adicionales del frontend
    """
    try:
        # Llamar al método reject con los datos adicionales
        result = DepositClass(db).reject(id, deposit_data)
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al rechazar depósito: {str(e)}")

@deposits.delete("/delete/{id}")
def delete(id: int, db: Session = Depends(get_db)):
    data = DepositClass(db).delete(id)

    return {"message": data}