from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import MachineTicketList
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