from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin, StoreManualSeat
from app.backend.classes.accountability_class import AccountabilityClass
from app.backend.auth.auth_user import get_current_active_user

accountability = APIRouter(
    prefix="/accountability",
    tags=["Accountability"]
)

@accountability.post("/store")
def store(manual_seat:StoreManualSeat, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AccountabilityClass(db).store(manual_seat.branch_office_id, manual_seat.expense_type_id, manual_seat.tax_status_id, manual_seat.period, manual_seat.amount)

    return {"message": data}

@accountability.get("/delete/{branch_office_id}/{period}")
def delete(branch_office_id: int, period: str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AccountabilityClass(db).delete(branch_office_id, period)

    return {"message": data}
