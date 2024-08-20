from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import OldEmployeeLaborDatum, UserLogin
from app.backend.classes.old_employee_labor_datum_class import OldEmployeeLaborDatumClass
from app.backend.classes.employee_labor_datum_class import EmployeeLaborDatumClass
from app.backend.auth.auth_user import get_current_active_user

old_employee_labor_data = APIRouter(
    prefix="/old_employee_labor_data",
    tags=["OldEmployeeLaborDatum"]
)

@old_employee_labor_data.post("/transfer")
def transfer(old_employee_labor_datum: OldEmployeeLaborDatum, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    old_employee_labor_datum_inputs = old_employee_labor_datum.dict()

    data = OldEmployeeLaborDatumClass(db).store(old_employee_labor_datum_inputs)

    if old_employee_labor_datum_inputs['end_document_type_id'] == 1:
        EmployeeLaborDatumClass(db).delete(old_employee_labor_datum_inputs["rut"])

    return {"message": data}

@old_employee_labor_data.get("/edit/{rut}")
def edit(rut:int,session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = OldEmployeeLaborDatumClass(db).get("rut", rut)

    return {"message": data}
