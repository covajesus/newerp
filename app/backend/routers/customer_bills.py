from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import GenerateCustomerBill, GeneratedCustomerBillList, CustomerBillList, GenerateCustomerCreditNoteBill, CustomerBillSearch, ToBeAcceptedCustomerBill, ChangeStatusInCustomerBill
from app.backend.classes.customer_bill_class import CustomerBillClass
from app.backend.classes.customer_class import CustomerClass
from app.backend.auth.auth_user import get_current_active_user
from app.backend.schemas import UserLogin

customer_bills = APIRouter(
    prefix="/customer_bills",
    tags=["CustomerBills"]
)

@customer_bills.post("/")
def index(customer_bill_inputs:CustomerBillList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CustomerBillClass(db).get_all(session_user.rol_id, session_user.rut, 1, customer_bill_inputs.page)

    return {"message": data}

@customer_bills.post("/search")
def search(customer_bills:CustomerBillSearch, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CustomerBillClass(db).search(session_user.rol_id, session_user.rut, customer_bills.branch_office_id, customer_bills.rut, customer_bills.customer, customer_bills.status_id, customer_bills.supervisor_id, customer_bills.page)

    return {"message": data}

@customer_bills.post("/store")
def store(customer_ticket_inputs:GenerateCustomerBill, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    existence_data = CustomerClass(db).check_existence(customer_ticket_inputs.rut)

    if customer_ticket_inputs.will_save == 1:
        if existence_data == 'Customer does not exist':
            CustomerClass(db).store(customer_ticket_inputs)
        else:
            CustomerClass(db).update(customer_ticket_inputs.rut, customer_ticket_inputs)

    data = CustomerBillClass(db).store(customer_ticket_inputs, session_user.rol_id)

    return {"message": data}

@customer_bills.post("/generate_bill")
def generate_bill(customer_bill_inputs:GenerateCustomerBill, db: Session = Depends(get_db)):
    existence_data = CustomerClass(db).check_existence(customer_bill_inputs.rut)

    if customer_bill_inputs.will_save == 1:
        if existence_data == 'Customer does not exist':
            CustomerClass(db).store(customer_bill_inputs)
        else:
            CustomerClass(db).update(customer_bill_inputs.rut, customer_bill_inputs)

    data = CustomerBillClass(db).generate(customer_bill_inputs)

    return {"message": data}

@customer_bills.post("/to_be_accepted")
def to_be_accepted(customer_bill_inputs:ToBeAcceptedCustomerBill, db: Session = Depends(get_db)):
    existence_data = CustomerClass(db).check_existence(customer_bill_inputs.rut)

    if customer_bill_inputs.will_save == 1:
        if existence_data == 'Customer does not exist':
            CustomerClass(db).store(customer_bill_inputs)
        else:
            CustomerClass(db).update(customer_bill_inputs.rut, customer_bill_inputs)

    data = CustomerBillClass(db).update(customer_bill_inputs)

    return {"message": data}

@customer_bills.post("/generated_bills")
def generated_tickets(customer_bill_inputs:GeneratedCustomerBillList, db: Session = Depends(get_db)):
    data = CustomerBillClass(db).get_all(2, customer_bill_inputs.page)

    return {"message": data}

@customer_bills.post("/generate_credit_note")
def generate_credit_note(customer_credit_note_bill_inputs:GenerateCustomerCreditNoteBill, db: Session = Depends(get_db)):
    data = CustomerBillClass(db).store_credit_note(customer_credit_note_bill_inputs)

    return {"message": data}

@customer_bills.get("/download/{id}")
def download(id:int, db: Session = Depends(get_db)):
    data = CustomerBillClass(db).download(id)

    return {"message": data}

@customer_bills.get("/verify/{id}")
def verify(id:int, db: Session = Depends(get_db)):
    data = CustomerBillClass(db).verify(id)

    return {"message": data}

@customer_bills.get("/edit/{id}")
def edit(id:int, db: Session = Depends(get_db)):
    data = CustomerBillClass(db).get(id)

    return {"message": data}

@customer_bills.get("/delete/{id}")
def delete(id:int, db: Session = Depends(get_db)):
    data = CustomerBillClass(db).delete(id)

    return {"message": data}

@customer_bills.get("/pre_accept/{id}")
def pre_accept(id:int, db: Session = Depends(get_db)):
    data = CustomerBillClass(db).pre_accept(id)

    return {"message": data}

@customer_bills.get("/reject/{id}")
def reject(id:int, db: Session = Depends(get_db)):
    data = CustomerBillClass(db).reject(id)

    return {"message": data}

@customer_bills.post("/change_status")
def change_status(customer_bill_inputs:ChangeStatusInCustomerBill, db: Session = Depends(get_db)):
    data = CustomerBillClass(db).change_status(customer_bill_inputs)

    return {"message": data}

@customer_bills.get("/check_payments")
def check_payments(db: Session = Depends(get_db)):
    data = CustomerBillClass(db).check_payments()

    return {"message": data}