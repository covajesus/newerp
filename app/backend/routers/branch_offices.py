from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import BranchOffice, UpdateBranchOffice, UserLogin
from app.backend.classes.branch_office_class import BranchOfficeClass
from app.backend.auth.auth_user import get_current_active_user

branch_offices = APIRouter(
    prefix="/branch_offices",
    tags=["BranchOffice"]
)

@branch_offices.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = BranchOfficeClass(db).get_all(session_user.rut, session_user.rol_id)

    return {"message": data}

@branch_offices.post("/store")
def store(branch_office:BranchOffice, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    branch_office_inputs = branch_office.dict()
    data = BranchOfficeClass(db).store(branch_office_inputs)

    return {"message": data}

@branch_offices.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = BranchOfficeClass(db).get("id", id)

    return {"message": data}

@branch_offices.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = BranchOfficeClass(db).delete(id)

    return {"message": data}

@branch_offices.patch("/update/{id}")
def update(id: int, branch_office: UpdateBranchOffice, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = BranchOfficeClass(db).update(id, branch_office)

    return {"message": data}