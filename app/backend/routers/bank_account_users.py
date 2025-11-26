from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.bank_account_user_class import BankAccountUserClass
from app.backend.schemas import BankAccountUser, StoreBankAccountUser, UpdateBankAccountUser, UserLogin
from app.backend.auth.auth_user import get_current_active_user

bank_account_users = APIRouter(
    prefix="/bank_account_users",
    tags=["BankAccountUsers"]
)

@bank_account_users.post("/")
def index(bank_account_user_inputs: BankAccountUser, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Obtener todos los usuarios de cuentas bancarias con paginación
    """
    data = BankAccountUserClass(db).get_all(session_user.id, bank_account_user_inputs.page)
    return {"message": data}

@bank_account_users.get("/")
def get_all(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Obtener todos los usuarios de cuentas bancarias sin paginación
    """
    data = BankAccountUserClass(db).get_all(session_user.id)
    return {"message": data}

@bank_account_users.get("/{id}")
def get_by_id(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Obtener un usuario de cuenta bancaria por ID
    """
    data = BankAccountUserClass(db).get(id)
    return {"message": data}

@bank_account_users.post("/get_by_rut/{rut}")
def get_by_rut(rut: str, db: Session = Depends(get_db)):
    """
    Obtener cuentas bancarias de usuario por RUT
    """
    data = BankAccountUserClass(db).get_by_rut(rut)
    return {"message": data}

@bank_account_users.post("/store")
def store(bank_account_user_inputs: StoreBankAccountUser, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Crear un nuevo usuario de cuenta bancaria
    """
    data = BankAccountUserClass(db).store(bank_account_user_inputs, session_user.id, session_user.rut)
    return {"message": data}

@bank_account_users.put("/update/{id}")
def update(id: int, bank_account_user_inputs: UpdateBankAccountUser, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Actualizar un usuario de cuenta bancaria existente
    """
    data = BankAccountUserClass(db).update(id, bank_account_user_inputs, session_user.id, session_user.rut)
    return {"message": data}

@bank_account_users.delete("/delete/{id}")
def delete(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Eliminar un usuario de cuenta bancaria
    """
    data = BankAccountUserClass(db).delete(id)
    return {"message": data}
