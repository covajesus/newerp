from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin
from app.backend.classes.accountability_class import AccountabilityClass
from app.backend.auth.auth_user import get_current_active_user

accountability = APIRouter(
    prefix="/accountability",
    tags=["Accountability"]
)

@accountability.get("/delete/{period}")
def index(period: str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AccountabilityClass(db).delete(period)

    return {"message": data}
