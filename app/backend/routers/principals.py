from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Principal, UpdatePrincipal, UserLogin
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

@principals.post("/store")
def store(principal:Principal, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    principal_inputs = principal.dict()
    data = PrincipalClass(db).store(principal_inputs)

    return {"message": data}

@principals.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PrincipalClass(db).get("id", id)

    return {"message": data}

@principals.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PrincipalClass(db).delete(id)

    return {"message": data}

@principals.patch("/update/{id}")
def update(id: int, principal: UpdatePrincipal, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PrincipalClass(db).update(id, principal)

    return {"message": data}