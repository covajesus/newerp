from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.old_employee_extra_datum_class import OldEmployeeExtraDatumClass
from app.backend.classes.employee_extra_datum_class import EmployeeExtraDatumClass
from app.backend.schemas import OldEmployeeExtra,UserLogin
from app.backend.auth.auth_user import get_current_active_user

old_employee_extras = APIRouter(
    prefix="/old_employee_extras",
    tags=["OldEmployeeExtras"]
)

@old_employee_extras.post("/transfer")
def transfer(old_employee_extra: OldEmployeeExtra, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    old_employee_extra_inputs = old_employee_extra.dict()

    data = OldEmployeeExtraDatumClass(db).store(old_employee_extra_inputs)

    # EmployeeExtraDatumClass(db).delete(old_employee_extra_inputs["rut"])

    return {"message": data}

@old_employee_extras.get("/edit/{rut}")
def edit(rut:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = OldEmployeeExtraDatumClass(db).get("rut", rut)

    return {"message": data}
