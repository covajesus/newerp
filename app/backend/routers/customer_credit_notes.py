from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import CustomerCreditNoteList, GeneratedCustomerCreditNoteList, CustomerCreditNoteSearch
from app.backend.classes.customer_credit_note_class import CustomerCreditNoteClass
from app.backend.auth.auth_user import get_current_active_user
from app.backend.schemas import UserLogin

customer_credit_notes = APIRouter(
    prefix="/customer_credit_notes",
    tags=["CustomerCreditNotes"]
)

@customer_credit_notes.post("/")
def index(customer_credit_note_inputs: CustomerCreditNoteList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CustomerCreditNoteClass(db).get_all(session_user.rol_id, session_user.rut, 1, customer_credit_note_inputs.page)

    return {"message": data}

@customer_credit_notes.post("/search")
def search(customer_credit_note_inputs: CustomerCreditNoteSearch, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CustomerCreditNoteClass(db).search(session_user.rol_id, session_user.rut, customer_credit_note_inputs.branch_office_id, customer_credit_note_inputs.rut, customer_credit_note_inputs.customer, customer_credit_note_inputs.status_id, customer_credit_note_inputs.supervisor_id, customer_credit_note_inputs.page)

    return {"message": data}

@customer_credit_notes.post("/generated_credit_notes")
def generated_credit_notes(customer_credit_note_inputs: GeneratedCustomerCreditNoteList, db: Session = Depends(get_db)):
    data = CustomerCreditNoteClass(db).get_all(2, customer_credit_note_inputs.page)

    return {"message": data}

@customer_credit_notes.get("/download/{id}")
def download(id: int, db: Session = Depends(get_db)):
    data = CustomerCreditNoteClass(db).download(id)

    return {"message": data}

@customer_credit_notes.get("/verify/{id}")
def verify(id: int, db: Session = Depends(get_db)):
    data = CustomerCreditNoteClass(db).verify(id)

    return {"message": data}

@customer_credit_notes.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    data = CustomerCreditNoteClass(db).get(id)

    return {"message": data}

@customer_credit_notes.get("/delete/{id}")
def delete(id: int, db: Session = Depends(get_db)):
    data = CustomerCreditNoteClass(db).delete(id)

    return {"message": data}

@customer_credit_notes.post("/change_status")
def change_status(customer_credit_note_inputs: CustomerCreditNoteSearch, db: Session = Depends(get_db)):
    data = CustomerCreditNoteClass(db).change_status(customer_credit_note_inputs.id)

    return {"message": data}
