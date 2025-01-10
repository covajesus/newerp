from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Customer, UpdateCustomer, UserLogin, CustomerList
from app.backend.classes.customer_class import CustomerClass
from app.backend.auth.auth_user import get_current_active_user

customers = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)

@customers.post("/")
def index(customer: CustomerList, db: Session = Depends(get_db)):

    data = CustomerClass(db).get_all(customer.rut, customer.page)

    return {"message": data}

@customers.post("/store")
def store(customer_inputs:Customer, db: Session = Depends(get_db)):
    data = CustomerClass(db).store(customer_inputs)

    return {"message": data}

@customers.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    data = CustomerClass(db).get(id)

    return {"message": data}

@customers.delete("/delete/{id}")
def delete(id:int, db: Session = Depends(get_db)):
    data = CustomerClass(db).delete(id)

    return {"message": data}

@customers.patch("/update/{id}")
def update(id: int, customer: UpdateCustomer, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CustomerClass(db).update(id, customer)

    return {"message": data}

@customers.get("/existence/{rut}")
def edit(rut: str, db: Session = Depends(get_db)):
    data = CustomerClass(db).check_existence(rut)

    return {"message": data}