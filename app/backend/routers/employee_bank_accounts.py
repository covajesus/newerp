from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import EmployeeBankAccount, UpdateEmployeeBankAccount, UserLogin, StoreEmployeeBankAccount
from app.backend.classes.employee_bank_account_class import EmployeeBankAccountClass
from app.backend.auth.auth_user import get_current_active_user

employee_bank_accounts = APIRouter(
    prefix="/employee_bank_accounts",
    tags=["EmployeeBankAccounts"]
)

@employee_bank_accounts.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EmployeeBankAccountClass(db).get_all()

    return {"message": data}

@employee_bank_accounts.post("/store")
def store(bank:StoreEmployeeBankAccount, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    bank_inputs = bank.dict()
    data = EmployeeBankAccountClass(db).store(bank_inputs)

    return {"message": data}

@employee_bank_accounts.get("/edit/{rut}")
def edit(rut:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EmployeeBankAccountClass(db).get("rut", rut)

    return {"message": data}

@employee_bank_accounts.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EmployeeBankAccountClass(db).delete(id)

    return {"message": data}

@employee_bank_accounts.patch("/update/{id}")
def update(id: int, employee_bank_account: UpdateEmployeeBankAccount, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    employee_bank_account = employee_bank_account.dict()
    
    data = EmployeeBankAccountClass(db).update(id, employee_bank_account)

    return {"message": data}