from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import CreateBranchOffice, UpdateBranchOffice, UserLogin
from app.backend.classes.branch_office_class import BranchOfficeClass
from app.backend.auth.auth_user import get_current_active_user

branch_offices = APIRouter(
    prefix="/branch_offices",
    tags=["BranchOffice"]
)

@branch_offices.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = BranchOfficeClass(db).get_all(session_user.rol_id, session_user.rut, session_user.branch_office_id)

    return {"message": data}

@branch_offices.get("/get_all_basement/")
def get_all_basement(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = BranchOfficeClass(db).get_all_basement(session_user.rol_id, session_user.rut, session_user.branch_office_id)

    return {"message": data}

@branch_offices.post("/get_full_data/")
def get_full_data(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = BranchOfficeClass(db).get_full_data()

    return {"message": data}

@branch_offices.post("/store")
def store(branch_office:CreateBranchOffice, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = BranchOfficeClass(db).store(branch_office)

    return {"message": data}

@branch_offices.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = BranchOfficeClass(db).get("id", id)

    return {"message": data}

@branch_offices.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = BranchOfficeClass(db).delete(id)

    return {"message": data}

@branch_offices.post("/update/")
def update(form_data: UpdateBranchOffice = Depends(UpdateBranchOffice.as_form), db: Session = Depends(get_db)):
    data = BranchOfficeClass(db).update(form_data)

    return {"message": data}