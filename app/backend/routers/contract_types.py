from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import ContractType, UpdateContractType, UserLogin
from app.backend.classes.contract_type_class import ContractTypeClass
from app.backend.auth.auth_user import get_current_active_user

contract_types = APIRouter(
    prefix="/contract_types",
    tags=["ContractTypes"]
)

@contract_types.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ContractTypeClass(db).get_all()

    return {"message": data}

@contract_types.post("/store")
def store(contract_type:ContractType, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    contract_type_inputs = contract_type.dict()
    data = ContractTypeClass(db).store(contract_type_inputs)

    return {"message": data}

@contract_types.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ContractTypeClass(db).get("id", id)

    return {"message": data}

@contract_types.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ContractTypeClass(db).delete(id)

    return {"message": data}

@contract_types.patch("/update/{id}")
def update(id: int, contract_type: UpdateContractType, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = ContractTypeClass(db).update(id, contract_type)

    return {"message": data}