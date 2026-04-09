from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.reference_type_class import ReferenceTypeClass
from app.backend.auth.auth_user import get_current_active_user
from app.backend.schemas import UserLogin

reference_types = APIRouter(
    prefix="/reference_types",
    tags=["ReferenceTypes"],
)


@reference_types.get("/")
def index(
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = ReferenceTypeClass(db).get_all()
    return {"message": data}
