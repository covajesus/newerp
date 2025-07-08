from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin, StoreManualSeat, StoreAccountability
from app.backend.classes.accountability_class import AccountabilityClass
from app.backend.auth.auth_user import get_current_active_user
from app.backend.classes.file_class import FileClass
from app.backend.classes.bank_statement_class import BankStatementClass
from fastapi import UploadFile, File, HTTPException
from datetime import datetime
import uuid

accountability = APIRouter(
    prefix="/accountability",
    tags=["Accountability"]
)

@accountability.post("/store")
def store(manual_seat:StoreManualSeat, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AccountabilityClass(db).store(manual_seat.branch_office_id, manual_seat.expense_type_id, manual_seat.tax_status_id, manual_seat.period, manual_seat.amount)

    return {"message": data}

@accountability.get("/delete/{branch_office_id}/{period}/{expense_type_id}")
def delete(branch_office_id: int, period: str, expense_type_id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AccountabilityClass(db).delete(branch_office_id, period, expense_type_id)

    return {"message": data}

@accountability.get("/subscriber_assets/store/{branch_office_id}/{period}")
def store_subscriber_assets(branch_office_id: int, period: str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AccountabilityClass(db).store_subscriber_assets(branch_office_id, period)

    return {"message": data}

@accountability.get("/subscriber_assets/delete/{branch_office_id}/{period}")
def delete_subscriber_assets(branch_office_id: int, period: str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AccountabilityClass(db).delete_subscriber_assets(branch_office_id, period)

    return {"message": data}

@accountability.post("/massive_store")
def store(
    support: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
        file_category_name = 'accountability'
        unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

        remote_path = f"{file_category_name}_{unique_filename}"

        message = FileClass(db).upload(support, remote_path)

        file_url = FileClass(db).get(remote_path)

        if file_extension == "xlsx":
            excel_data = AccountabilityClass(db).read_store_massive_accountability(file_url)
        else:
            raise HTTPException(status_code=400, detail="Formato no compatible")

        return {"message": message, "file_url": file_url, "data": excel_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")
