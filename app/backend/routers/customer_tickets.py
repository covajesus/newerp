from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import GenerateCustomerTicket, GeneratedCustomerTicketList, CustomerTicketList, GenerateCustomerCreditNoteTicket, CustomerTicketSearch, ToBeAcceptedCustomerTicket, ChangeStatusInCustomerTicket
from app.backend.classes.customer_ticket_class import CustomerTicketClass
from app.backend.classes.customer_class import CustomerClass
from app.backend.auth.auth_user import get_current_active_user
from app.backend.schemas import UserLogin

customer_tickets = APIRouter(
    prefix="/customer_tickets",
    tags=["CustomerTickets"]
)

@customer_tickets.post("/")
def index(customer_ticket_inputs:CustomerTicketList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CustomerTicketClass(db).get_all(session_user.rol_id, session_user.rut, 1, customer_ticket_inputs.page)

    return {"message": data}

@customer_tickets.post("/search")
def search(customer_ticket_inputs:CustomerTicketSearch, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CustomerTicketClass(db).search(session_user.rol_id, session_user.rut, customer_ticket_inputs.branch_office_id, customer_ticket_inputs.rut,  customer_ticket_inputs.customer, customer_ticket_inputs.status_id, customer_ticket_inputs.supervisor_id, customer_ticket_inputs.page)

    return {"message": data}

@customer_tickets.post("/generate_ticket")
def generate_ticket(customer_ticket_inputs:GenerateCustomerTicket, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    existence_data = CustomerClass(db).check_existence(customer_ticket_inputs.rut)

    if customer_ticket_inputs.will_save == 1:
        if existence_data == 'Customer does not exist':
            CustomerClass(db).store(customer_ticket_inputs)
        else:
            CustomerClass(db).update(customer_ticket_inputs.rut, customer_ticket_inputs)

    data = CustomerTicketClass(db).generate(customer_ticket_inputs)

    return {"message": data}

@customer_tickets.post("/store")
def store(customer_ticket_inputs:GenerateCustomerTicket, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    existence_data = CustomerClass(db).check_existence(customer_ticket_inputs.rut)

    if customer_ticket_inputs.will_save == 1:
        if existence_data == 'Customer does not exist':
            CustomerClass(db).store(customer_ticket_inputs)
        else:
            CustomerClass(db).update(customer_ticket_inputs.rut, customer_ticket_inputs)

    data = CustomerTicketClass(db).store(customer_ticket_inputs, session_user.rol_id)

    return {"message": data}

@customer_tickets.get("/pre_accept/{id}")
def pre_accept(id:int, db: Session = Depends(get_db)):
    data = CustomerTicketClass(db).pre_accept(id)

    return {"message": data}

@customer_tickets.post("/generate_credit_note")
def generate_credit_note(customer_credit_note_ticket_inputs:GenerateCustomerCreditNoteTicket, db: Session = Depends(get_db)):
    data = CustomerTicketClass(db).store_credit_note(customer_credit_note_ticket_inputs)

    return {"message": data}

@customer_tickets.post("/to_be_accepted")
def to_be_accepted(customer_ticket_inputs:ToBeAcceptedCustomerTicket, db: Session = Depends(get_db)):
    existence_data = CustomerClass(db).check_existence(customer_ticket_inputs.rut)

    if customer_ticket_inputs.will_save == 1:
        if existence_data == 'Customer does not exist':
            CustomerClass(db).store(customer_ticket_inputs)
        else:
            CustomerClass(db).update(customer_ticket_inputs.rut, customer_ticket_inputs)

    data = CustomerTicketClass(db).update(customer_ticket_inputs)

    return {"message": data}

@customer_tickets.post("/generated_tickets")
def generated_tickets(customer_ticket_inputs:GeneratedCustomerTicketList, db: Session = Depends(get_db)):
    data = CustomerTicketClass(db).get_all(2, customer_ticket_inputs.page)

    return {"message": data}

@customer_tickets.get("/download/{id}")
def download(id:int, db: Session = Depends(get_db)):
    data = CustomerTicketClass(db).download(id)

    return {"message": data}

@customer_tickets.get("/verify/{id}")
def verify(id:int, db: Session = Depends(get_db)):
    data = CustomerTicketClass(db).verify(id)

    return {"message": data}

@customer_tickets.get("/edit/{id}")
def edit(id:int, db: Session = Depends(get_db)):
    data = CustomerTicketClass(db).get(id)

    return {"message": data}

@customer_tickets.get("/delete/{id}")
def delete(id:int, db: Session = Depends(get_db)):
    data = CustomerTicketClass(db).delete(id)

    return {"message": data}

@customer_tickets.get("/reject/{id}")
def reject(id:int, db: Session = Depends(get_db)):
    data = CustomerTicketClass(db).reject(id)

    return {"message": data}

@customer_tickets.post("/change_status")
def change_status(customer_ticket_inputs:ChangeStatusInCustomerTicket, db: Session = Depends(get_db)):
    data = CustomerTicketClass(db).change_status(customer_ticket_inputs)

    return {"message": data}

@customer_tickets.get("/check_payments")
def check_payments(db: Session = Depends(get_db)):
    data = CustomerTicketClass(db).check_payments()

    return {"message": data}