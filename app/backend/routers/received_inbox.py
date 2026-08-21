from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.backend.db.database import get_db
from app.backend.schemas import (
    ReceivedTributaryDocumentList,
    ReceivedDteList,
    ReceivedInboxAcknowledgment,
    ReceivedInboxImportDay,
)
from app.backend.classes.received_inbox_class import ReceivedInboxClass

received_inbox = APIRouter(
    prefix="/received_inbox",
    tags=["ReceivedInbox"]
)


@received_inbox.post("/")
def index(received_inbox_inputs: ReceivedTributaryDocumentList, db: Session = Depends(get_db)):
    data = ReceivedInboxClass(db).get_all(received_inbox_inputs.page)
    return {"message": data}


@received_inbox.post("/search")
def search(received_inbox_inputs: ReceivedDteList, db: Session = Depends(get_db)):
    data = ReceivedInboxClass(db).search(
        received_inbox_inputs.folio,
        received_inbox_inputs.branch_office_id,
        received_inbox_inputs.rut,
        received_inbox_inputs.supplier,
        received_inbox_inputs.since,
        received_inbox_inputs.until,
        received_inbox_inputs.amount,
        received_inbox_inputs.status_id,
        received_inbox_inputs.dte_type_id,
        received_inbox_inputs.page,
    )
    return {"message": data}


@received_inbox.get("/refresh")
def refresh(db: Session = Depends(get_db)):
    data = ReceivedInboxClass(db).refresh()
    return {"message": data}


@received_inbox.get("/import_plan")
def import_plan(db: Session = Depends(get_db)):
    data = ReceivedInboxClass(db).import_plan()
    return {"message": data}


@received_inbox.post("/import_day")
def import_day(received_inbox_inputs: ReceivedInboxImportDay, db: Session = Depends(get_db)):
    data = ReceivedInboxClass(db).import_day(
        received_inbox_inputs.date,
        received_inbox_inputs.consolidate,
    )
    return {"message": data}


@received_inbox.post("/acknowledge")
def acknowledge(received_inbox_inputs: ReceivedInboxAcknowledgment, db: Session = Depends(get_db)):
    data = ReceivedInboxClass(db).acknowledge(received_inbox_inputs)
    return {"message": data}


@received_inbox.get("/download/{id}")
def download(id: int, db: Session = Depends(get_db)):
    data = ReceivedInboxClass(db).download_pdf(id)
    return {"message": data}
