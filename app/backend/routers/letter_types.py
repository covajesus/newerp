from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import LetterType, UpdateLetterType, UserLogin
from app.backend.classes.letter_type_class import LetterTypeClass
from app.backend.auth.auth_user import get_current_active_user

letter_types = APIRouter(
    prefix="/letter_types",
    tags=["LetterTypes"]
)

@letter_types.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = LetterTypeClass(db).get_all()

    return {"message": data}

@letter_types.post("/store")
def store(bank:LetterType, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    bank_inputs = bank.dict()
    data = LetterTypeClass(db).store(bank_inputs)

    return {"message": data}

@letter_types.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = LetterTypeClass(db).get("id", id)

    return {"message": data}

@letter_types.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = LetterTypeClass(db).delete(id)

    return {"message": data}

@letter_types.patch("/update/{id}")
def update(id: int, bank: UpdateLetterType, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = LetterTypeClass(db).update(id, bank)

    return {"message": data}