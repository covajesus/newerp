from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import GenerateCustomerBill, GeneratedCustomerBillList, CustomerBillList
from app.backend.classes.customer_bill_class import CustomerBillClass
from app.backend.classes.customer_class import CustomerClass

customer_bills = APIRouter(
    prefix="/customer_bills",
    tags=["CustomerBills"]
)

@customer_bills.post("/")
def index(customer_ticket_inputs:CustomerBillList, db: Session = Depends(get_db)):
    data = CustomerBillClass(db).get_all(1, customer_ticket_inputs.page)

    return {"message": data}

@customer_bills.post("/generate_bill")
def store(customer_ticket_inputs:GenerateCustomerBill, db: Session = Depends(get_db)):
    data = CustomerBillClass(db).store(customer_ticket_inputs)

    CustomerClass(db).update(customer_ticket_inputs.rut, customer_ticket_inputs)

    return {"message": data}

@customer_bills.post("/generated_bills")
def generated_tickets(customer_ticket_inputs:GeneratedCustomerBillList, db: Session = Depends(get_db)):
    data = CustomerBillClass(db).get_all(2, customer_ticket_inputs.page)

    return {"message": data}

@customer_bills.get("/download/{id}")
def download(id:int, db: Session = Depends(get_db)):
    data = CustomerBillClass(db).download(id)
    print(data)

    return {"message": data}

@customer_bills.get("/verify/{id}")
def verify(id:int, db: Session = Depends(get_db)):
    data = CustomerBillClass(db).verify(id)

    return {"message": data}

@customer_bills.get("/edit/{id}")
def download(id:int, db: Session = Depends(get_db)):
    data = CustomerBillClass(db).get(id)

    return {"message": data}

@customer_bills.get("/download/{id}")
def download(id: int, db: Session = Depends(get_db)):
    pdf_content = CustomerBillClass(db).download(id)

    return pdf_content