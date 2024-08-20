from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import CivilState, UpdateCivilState, UserLogin
from app.backend.classes.employee_type_class import EmployeeTypeClass
from app.backend.auth.auth_user import get_current_active_user

employee_types = APIRouter(
    prefix="/employee_types",
    tags=["Employee Types"]
)

@employee_types.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EmployeeTypeClass(db).get_all()

    return {"message": data}