from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import GenerateCustomerTicket, GeneratedCustomerTicketList, CustomerTicketList
from app.backend.classes.customer_ticket_class import CustomerTicketClass
from app.backend.classes.customer_class import CustomerClass

customer_tickets = APIRouter(
    prefix="/customer_tickets",
    tags=["CustomerTickets"]
)

@customer_tickets.post("/")
def index(customer_ticket_inputs:CustomerTicketList, db: Session = Depends(get_db)):
    data = CustomerTicketClass(db).get_all(1, customer_ticket_inputs.page)

    return {"message": data}

@customer_tickets.post("/generate_ticket")
def store(customer_ticket_inputs:GenerateCustomerTicket, db: Session = Depends(get_db)):
    existence_data = CustomerClass(db).check_existence(customer_ticket_inputs.rut)

    if existence_data == 'Customer does not exist':
        CustomerClass(db).store(customer_ticket_inputs)
    else:
        CustomerClass(db).update(customer_ticket_inputs.rut, customer_ticket_inputs)

    data = CustomerTicketClass(db).store(customer_ticket_inputs)

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
def download(id:int, db: Session = Depends(get_db)):
    data = CustomerTicketClass(db).get(id)

    return {"message": data}

@customer_tickets.get("/download/{id}")
def download(id: int, db: Session = Depends(get_db)):
    pdf_content = CustomerTicketClass(db).download(id)

    return pdf_content