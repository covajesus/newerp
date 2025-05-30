from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin
from app.backend.classes.principal_class import PrincipalClass
from app.backend.auth.auth_user import get_current_active_user

principals = APIRouter(
    prefix="/principals",
    tags=["Principals"]
)

@principals.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PrincipalClass(db).get_all()

    return {"message": data}