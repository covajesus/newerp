from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Rol, UpdateRol, UserLogin
from app.backend.classes.rol_class import RolClass
from app.backend.auth.auth_user import get_current_active_user
from app.backend.classes.social_law_class import SocialLawClass

social_laws = APIRouter(
    prefix="/social_laws",
    tags=["SocialLaws"]
)

@social_laws.get("/calculate/{period}")
def store(period:str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = SocialLawClass(db).calculate(period)

    return {"message": data}

@social_laws.get("/totals/{period}")
def store(period:str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = SocialLawClass(db).get_totals(period)

    return {"message": data}

@social_laws.get("/movements/{period}")
def store(period:str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = SocialLawClass(db).movements(period)

    return {"message": data}