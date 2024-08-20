from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Bank, UpdateBank, UserLogin
from app.backend.classes.bank_class import BankClass
from app.backend.auth.auth_user import get_current_active_user

banks = APIRouter(
    prefix="/banks",
    tags=["Bank"]
)

@banks.post("/")
def index(db: Session = Depends(get_db)):

    data = BankClass(db).get_all()

    return {"message": data}

@banks.post("/store")
def store(bank:Bank, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    bank_inputs = bank.dict()
    data = BankClass(db).store(bank_inputs)

    return {"message": data}

@banks.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = BankClass(db).get("id", id)

    return {"message": data}

@banks.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = BankClass(db).delete(id)

    return {"message": data}

@banks.patch("/update/{id}")
def update(id: int, bank: UpdateBank, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = BankClass(db).update(id, bank)

    return {"message": data}