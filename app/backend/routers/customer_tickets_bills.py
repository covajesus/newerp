from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import GeneratedCustomerTicketBillList, CustomerTicketBillList, GenerateCustomerCreditNoteTicketBill, CustomerTicketBillSearch, ToBeAcceptedCustomerTicketBill, ChangeStatusInCustomerTicketBill
from app.backend.classes.customer_ticket_bill_class import CustomerTicketBillClass
from app.backend.classes.customer_class import CustomerClass
from app.backend.auth.auth_user import get_current_active_user
from app.backend.schemas import UserLogin

customer_tickets_bills = APIRouter(
    prefix="/customer_tickets_bills",
    tags=["CustomerTicketsBills"]
)

@customer_tickets_bills.post("/")
def index(customer_ticket_inputs:CustomerTicketBillList, db: Session = Depends(get_db)):
    data = CustomerTicketBillClass(db).get_all(customer_ticket_inputs.page)

    return {"message": data}

@customer_tickets_bills.post("/search")
def search(customer_ticket_bill_inputs:CustomerTicketBillSearch, db: Session = Depends(get_db)):
    data = CustomerTicketBillClass(db).search(customer_ticket_bill_inputs.branch_office_id, customer_ticket_bill_inputs.rut, customer_ticket_bill_inputs.status_id, customer_ticket_bill_inputs.supervisor_id, customer_ticket_bill_inputs.page)

    return {"message": data}

@customer_tickets_bills.post("/generate_credit_note")
def generate_credit_note(customer_credit_note_ticket_bill_inputs:GenerateCustomerCreditNoteTicketBill, db: Session = Depends(get_db)):
    data = CustomerTicketBillClass(db).store_credit_note(customer_credit_note_ticket_bill_inputs)

    return {"message": data}

@customer_tickets_bills.post("/to_be_accepted")
def to_be_accepted(customer_ticket_bill_inputs:ToBeAcceptedCustomerTicketBill, db: Session = Depends(get_db)):
    existence_data = CustomerClass(db).check_existence(customer_ticket_bill_inputs.rut)

    if customer_ticket_bill_inputs.will_save == 1:
        if existence_data == 'Customer does not exist':
            CustomerClass(db).store(customer_ticket_bill_inputs)
        else:
            CustomerClass(db).update(customer_ticket_bill_inputs.rut, customer_ticket_bill_inputs)

    data = CustomerTicketBillClass(db).update(customer_ticket_bill_inputs)

    return {"message": data}

@customer_tickets_bills.post("/generated_tickets_bills")
def generated_tickets_bills(customer_ticket_bill_inputs:GeneratedCustomerTicketBillList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CustomerTicketBillClass(db).get_all(session_user.rol_id, session_user.rut, customer_ticket_bill_inputs.page)

    return {"message": data}

@customer_tickets_bills.post("/dtes_to_review")
def dtes_to_review(customer_ticket_bill_inputs:GeneratedCustomerTicketBillList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CustomerTicketBillClass(db).get_all_to_review(session_user.rol_id, session_user.rut, customer_ticket_bill_inputs.page)

    return {"message": data}

@customer_tickets_bills.get("/download/{id}")
def download(id:int, db: Session = Depends(get_db)):
    data = CustomerTicketBillClass(db).download(id)

    return {"message": data}

@customer_tickets_bills.get("/verify/{id}")
def verify(id:int, db: Session = Depends(get_db)):
    data = CustomerTicketBillClass(db).verify(id)

    return {"message": data}

@customer_tickets_bills.get("/edit/{id}")
def edit(id:int, db: Session = Depends(get_db)):
    data = CustomerTicketBillClass(db).get(id)

    return {"message": data}

@customer_tickets_bills.get("/accept_dte_deposit_transfer/{id}")
def accept_dte_deposit_transfer(id:int, db: Session = Depends(get_db)):
    data = CustomerTicketBillClass(db).accept_dte_payment(id)

    return {"message": data}

@customer_tickets_bills.get("/reject_dte_deposit_transfer/{id}")
def reject_dte_deposit_transfer(id:int, db: Session = Depends(get_db)):
    data = CustomerTicketBillClass(db).reject_dte_payment(id)

    return {"message": data}

@customer_tickets_bills.get("/delete/{id}")
def delete(id:int, db: Session = Depends(get_db)):
    data = CustomerTicketBillClass(db).delete(id)

    return {"message": data}

@customer_tickets_bills.get("/reject/{id}")
def reject(id:int, db: Session = Depends(get_db)):
    data = CustomerTicketBillClass(db).reject(id)

    return {"message": data}

@customer_tickets_bills.post("/change_status")
def change_status(customer_ticket_bill_inputs:ChangeStatusInCustomerTicketBill, db: Session = Depends(get_db)):
    data = CustomerTicketBillClass(db).change_status(customer_ticket_bill_inputs)

    return {"message": data}