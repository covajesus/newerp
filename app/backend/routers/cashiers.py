from fastapi import APIRouter, Depends
from app.backend.db.database import get_db, get_db2
from sqlalchemy.orm import Session
from app.backend.classes.cashier_class import CashierClass
from app.backend.schemas import CashierList, StoreCashier, SearchCashier
from app.backend.auth.auth_user import get_current_active_user
from app.backend.schemas import UserLogin

cashiers = APIRouter(
    prefix="/cashiers",
    tags=["Cashiers"]
)

@cashiers.get("/{branch_office_id}")
def index(branch_office_id:int, db: Session = Depends(get_db)):
    if branch_office_id != -1:
        data = CashierClass(db).get_all(branch_office_id)
    else:
        data = CashierClass(db).get_all()

    return {"message": data}

@cashiers.post("/all")
def all(db: Session = Depends(get_db)):
    data = CashierClass(db).get_all()

    return {"message": data}

@cashiers.post("/latest_update")
def latest_update(db: Session = Depends(get_db)):
    data = CashierClass(db).latest_update()

    return {"message": data}

@cashiers.post("/get_list")
def get_list(cashier: CashierList, db: Session = Depends(get_db)):
    data = CashierClass(db).get_list(cashier.page)

    return {"message": data}

@cashiers.post("/store")
def store(cashier_inputs: StoreCashier, db: Session = Depends(get_db)):
    data = CashierClass(db).store(cashier_inputs)

    return {"message": data}

@cashiers.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CashierClass(db).get("id", id)

    return {"message": data}

@cashiers.post("/update/{id}")
def update(id:int, cashier_inputs: StoreCashier, db: Session = Depends(get_db)):
    data = CashierClass(db).update(id, cashier_inputs)

    return {"message": data}

@cashiers.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CashierClass(db).delete(id)

    return {"message": data}

@cashiers.post("/search")
def edit(cashier_inputs:SearchCashier, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CashierClass(db).search(cashier_inputs, cashier_inputs.page)

    return {"message": data}

@cashiers.get("/available_folios/cron")
def available_folios_cron(db: Session = Depends(get_db), db2: Session = Depends(get_db2)):
    data = CashierClass(db2).get_all_cashiers()

    CashierClass(db).update_all_cashiers(data)

    return {"message": 'Updated o inserted cashiers in the second database.'}