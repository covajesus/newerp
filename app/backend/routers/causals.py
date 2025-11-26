from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin
from app.backend.classes.causals_class import CausalClass
from app.backend.auth.auth_user import get_current_active_user

causals = APIRouter(
    prefix="/causals",
    tags=["Causal"]
)

@causals.get("/{id}")
def index(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if id != -1:
        data = CausalClass(db).get_all('end_document_status_id', id)
    else:
        data = CausalClass(db).get_all()

    return {"message": data}

@causals.get("/")
def  index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CausalClass(db).get()

    return {'message': data}
