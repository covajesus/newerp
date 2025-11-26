from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Gender, UpdateGender, UserLogin
from app.backend.classes.gender_class import GenderClass
from app.backend.auth.auth_user import get_current_active_user

genders = APIRouter(
    prefix="/genders",
    tags=["Genders"]
)

@genders.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = GenderClass(db).get_all()

    return {"message": data}

@genders.post("/store")
def store(gender:Gender, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    gender_inputs = gender.dict()
    data = GenderClass(db).store(gender_inputs)

    return {"message": data}

@genders.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = GenderClass(db).get("id", id)

    return {"message": data}

@genders.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = GenderClass(db).delete(id)

    return {"message": data}

@genders.patch("/update/{id}")
def update(id: int, gender: UpdateGender, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = GenderClass(db).update(id, gender)

    return {"message": data}