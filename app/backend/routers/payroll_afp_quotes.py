from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin
from app.backend.classes.payroll_afp_quote_indicator_class import PayrollAfpQuoteIndicatorClass
from app.backend.auth.auth_user import get_current_active_user

payroll_afp_quotes = APIRouter(
    prefix="/payroll_afp_quotes",
    tags=["PayrollAfpQoutes"]
)

@payroll_afp_quotes.get("/{pention_id}/{period}")
def index(pention_id:int, period:str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PayrollAfpQuoteIndicatorClass(db).get(pention_id, period)

    return {"message": data}