from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Nationality, UpdateNationality, UserLogin
from app.backend.classes.nationality_class import NationalityClass
from app.backend.auth.auth_user import get_current_active_user

nationalities = APIRouter(
    prefix="/nationalities",
    tags=["Nationalities"]
)

@nationalities.get("/")
def index(user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = NationalityClass(db).get_all()

    return {"message": data}

@nationalities.post("/store")
def store(nationality:Nationality, user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    nationality_inputs = nationality.dict()
    data = NationalityClass(db).store(nationality_inputs)

    return {"message": data}

@nationalities.get("/edit/{id}")
def edit(id:int, user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = NationalityClass(db).get("id", id)

    return {"message": data}

@nationalities.delete("/delete/{id}")
def delete(id:int, user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = NationalityClass(db).delete(id)

    return {"message": data}

@nationalities.patch("/update/{id}")
def update(id: int, nationality: UpdateNationality, user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = NationalityClass(db).update(id, nationality)

    return {"message": data}