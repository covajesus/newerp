from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin
from app.backend.classes.sinister_type_class import SinisterTypeClass
from app.backend.auth.auth_user import get_current_active_user

sinister_types = APIRouter(
    prefix="/sinister_types",
    tags=["SinisterTypes"]
)

@sinister_types.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Obtiene todos los tipos de siniestros
    """
    data = SinisterTypeClass(db).get_all()
    return {"message": data}
