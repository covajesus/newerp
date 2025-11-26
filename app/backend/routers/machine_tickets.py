from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import MachineTicketList, GenerateMachineCreditNoteTicket, MachineTicketSearch
from app.backend.classes.machine_ticket_class import MachineTicketClass

machine_tickets = APIRouter(
    prefix="/machine_tickets",
    tags=["MachineTickets"]
)

@machine_tickets.post("/")
def index(machine_ticket_inputs:MachineTicketList, db: Session = Depends(get_db)):
    data = MachineTicketClass(db).get_all(machine_ticket_inputs.page)

    return {"message": data}

@machine_tickets.get("/download/{id}")
def download(id:int, db: Session = Depends(get_db)):
    data = MachineTicketClass(db).download(id)

    return {"message": data}

@machine_tickets.post("/generate_credit_note")
def generate_credit_note(machine_credit_note_ticket_inputs:GenerateMachineCreditNoteTicket, db: Session = Depends(get_db)):
    data = MachineTicketClass(db).store_credit_note(machine_credit_note_ticket_inputs)

    return {"message": data}

@machine_tickets.post("/search")
def search(machine_ticket_inputs: MachineTicketSearch, db: Session = Depends(get_db)):
    data = MachineTicketClass(db).search(machine_ticket_inputs.folio, machine_ticket_inputs.branch_office_id, machine_ticket_inputs.dte_type_id, machine_ticket_inputs.amount, machine_ticket_inputs.since, machine_ticket_inputs.until, machine_ticket_inputs.page)

    return {"message": data}