from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import AccountType, UpdateAccountType, UserLogin
from app.backend.classes.account_type_class import AccountTypeClass
from app.backend.auth.auth_user import get_current_active_user

account_types = APIRouter(
    prefix="/account_types",
    tags=["AccountType"]
)

@account_types.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AccountTypeClass(db).get_all()

    return {"message": data}

@account_types.post("/store")
def store(bank:AccountType, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    bank_inputs = bank.dict()
    data = AccountTypeClass(db).store(bank_inputs)

    return {"message": data}

@account_types.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AccountTypeClass(db).get("id", id)

    return {"message": data}

@account_types.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AccountTypeClass(db).delete(id)

    return {"message": data}

@account_types.patch("/update/{id}")
def update(id: int, bank: UpdateAccountType, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AccountTypeClass(db).update(id, bank)

    return {"message": data}