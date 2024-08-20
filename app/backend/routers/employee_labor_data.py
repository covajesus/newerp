from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import EmployeeLaborDatum, UpdateEmployeeLaborDatum, UserLogin
from app.backend.classes.employee_labor_datum_class import EmployeeLaborDatumClass
from app.backend.auth.auth_user import get_current_active_user

employee_labor_data = APIRouter(
    prefix="/employee_labor_data",
    tags=["Employee_Labor_Data"]
)

@employee_labor_data.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EmployeeLaborDatumClass(db).get_all()

    return {"message": data}

@employee_labor_data.get("/active_employee_totals")
def active_employee_total(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EmployeeLaborDatumClass(db).active_employee_total()

    return {"message": data}

@employee_labor_data.get("/distribution_totals")
def distribution_total(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EmployeeLaborDatumClass(db).distribution_totals()

    return {"message": data}

@employee_labor_data.post("/store")
def store(employee_labor_datum:EmployeeLaborDatum, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    employee_labor_datum_inputs = employee_labor_datum.dict()
    data = EmployeeLaborDatumClass(db).store(employee_labor_datum_inputs)

    return {"message": data}

@employee_labor_data.get("/edit/{rut}")
def edit(rut:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EmployeeLaborDatumClass(db).get("rut", rut)
    return {"message": data}

@employee_labor_data.get("/edit/branch/{branch_office}")
def get_by_Branch_office(branch_office:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EmployeeLaborDatumClass(db).get_all_by_branch_office(branch_office)
    return {"message": data}

@employee_labor_data.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EmployeeLaborDatumClass(db).delete(id)

    return {"message": data}

@employee_labor_data.patch("/update/{id}")
def update(id: int, employee_labor_datum: UpdateEmployeeLaborDatum, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    employee_labor_datum_inputs = employee_labor_datum.dict()
    data = EmployeeLaborDatumClass(db).update(id, employee_labor_datum_inputs)

    return {"message": data}