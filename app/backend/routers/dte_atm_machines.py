from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import DteAtmMachine, UserLogin
from app.backend.classes.dte_atm_machine_class import DteAtmMachineClass
from app.backend.auth.auth_user import get_current_active_user

dte_atm_machines = APIRouter(
    prefix="/dte_atm_machines",
    tags=["DteAtmMachine"]
)

@dte_atm_machines.post("/store")
def index(dte_atm_machine:DteAtmMachine, db: Session = Depends(get_db)):
    dte_atm_machine_inputs = dte_atm_machine.dict()
    
    data = DteAtmMachineClass(db).store(dte_atm_machine_inputs)
    
    return {"message": data}