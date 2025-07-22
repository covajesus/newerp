from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.file_class import FileClass
from app.backend.schemas import BankStatement, DepositIds
from fastapi import UploadFile, File, HTTPException
from app.backend.classes.bank_statement_class import BankStatementClass
from datetime import datetime
import uuid

bank_statements = APIRouter(
    prefix="/bank_statements",
    tags=["BankStatement"]
)

@bank_statements.get("/compare_update_deposits")
def compare_update_deposits(
    db: Session = Depends(get_db)
):
    BankStatementClass(db).compare_update_deposits()

    return {"message": 'Uploaded successfully'}

@bank_statements.post("/get_comparation_pending_dtes_bank_statements")
def get_comparation_pending_dtes_bank_statements(
    db: Session = Depends(get_db)
):
    bank_statements = BankStatementClass(db).get_comparation_pending_dtes_bank_statements()

    return {"message": bank_statements}

@bank_statements.post("/get_comparation_pending_deposits_bank_statements")
def get_comparation_pending_deposits_bank_statements(
    db: Session = Depends(get_db)
):
    bank_statements = BankStatementClass(db).get_comparation_pending_deposits_bank_statements()

    return {"message": bank_statements}

@bank_statements.post("/store")
def store(
    form_data: BankStatement = Depends(BankStatement.as_form),
    support: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
        file_category_name = 'bank_statements'
        unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

        remote_path = f"{file_category_name}_{unique_filename}"

        message = FileClass(db).upload(support, remote_path)

        file_url = FileClass(db).get(remote_path)

        if file_extension == "xlsx":
            excel_data = BankStatementClass(db).read_store_bank_statement(file_url, form_data.period)
        else:
            raise HTTPException(status_code=400, detail="Formato no compatible")

        return {"message": message, "file_url": file_url, "data": excel_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")

@bank_statements.get("/customer/accept/{id}/{payment_date}")
def customer_accept(
    id: int,
    payment_date: str,
    db: Session = Depends(get_db)
):
    message = BankStatementClass(db).customer_accept(id, payment_date)

    return {"message": message}

@bank_statements.get("/deposit/accept/{id}")
def deposit_accept(
    id: int,
    db: Session = Depends(get_db)
):
    message = BankStatementClass(db).deposit_accept(id)

    return {"message": message}

@bank_statements.post("/deposit/massive_accept")
def massive_accept(data: DepositIds, db: Session = Depends(get_db)):
    results = []
    
    for deposit_id in data.deposit_ids:
        response = BankStatementClass(db).deposit_accept(deposit_id)
        results.append({"id": deposit_id, "message": response})

    return {"message": "Depósitos procesados correctamente", "details": results}