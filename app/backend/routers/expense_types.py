from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.expense_type_class import ExpenseTypeClass
from app.backend.schemas import ExpenseType, StoreExpenseType, UpdateExpenseType

expense_types = APIRouter(
    prefix="/expense_types",
    tags=["ExpenseTypes"]
)

@expense_types.post("/")
def index(expense_type_inputs: ExpenseType, db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).get_list(expense_type_inputs.page)

    return {"message": data}

@expense_types.get("/")
def index(db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).get_all()

    return {"message": data}

@expense_types.get("/capitulation_visibles")
def capitulation_visibles(db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).get_all_capitulation_visibles()

    return {"message": data}

@expense_types.get("/eerr_visibles")
def eerr_visibles(db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).get_all_eerr_visibles()

    return {"message": data}

@expense_types.post("/store")
def store(expense_type_inputs: StoreExpenseType, db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).store(expense_type_inputs)
    return {"message": data}

@expense_types.delete("/delete/{id}")
def delete(id: int, db: Session = Depends(get_db)):
    ExpenseTypeClass(db).delete(id)

    return {"message": "success"}

@expense_types.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).get(id)

    return {"message": data}

@expense_types.post("/update")
def post(update_expense_type: UpdateExpenseType, db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).update(update_expense_type)

    return {"message": data}
