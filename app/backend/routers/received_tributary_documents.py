from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import ReceivedTributaryDocumentList, ChangeStatusReceivedTributaryDocument, ReceivedTributaryDocumentToPay
from app.backend.classes.received_tributary_document_class import ReceivedTributaryDocumentClass

received_tributary_documents = APIRouter(
    prefix="/received_tributary_documents",
    tags=["ReceivedTributaryDocuments"]
)

@received_tributary_documents.post("/")
def index(received_tributary_document_inputs:ReceivedTributaryDocumentList, db: Session = Depends(get_db)):
    data = ReceivedTributaryDocumentClass(db).get_all(received_tributary_document_inputs.page)

    return {"message": data}

@received_tributary_documents.post("/pay")
def pay(received_tributary_document_inputs:ReceivedTributaryDocumentToPay, db: Session = Depends(get_db)):
    data = ReceivedTributaryDocumentClass(db).pay(received_tributary_document_inputs)

    return {"message": data}

@received_tributary_documents.post("/all_supplier_bills/{rut}")
def all_supplier_bills(rut:str, db: Session = Depends(get_db)):
    data = ReceivedTributaryDocumentClass(db).get_all_supplier_bills(rut)

    return {"message": data}

@received_tributary_documents.get("/refresh")
def refresh(db: Session = Depends(get_db)):
    data = ReceivedTributaryDocumentClass(db).refresh()

    return {"message": data}

@received_tributary_documents.post("/change_status")
def change_status(received_tributary_document_inputs:ChangeStatusReceivedTributaryDocument, db: Session = Depends(get_db)):
    data = ReceivedTributaryDocumentClass(db).change_status(received_tributary_document_inputs)

    return {"message": data}

@received_tributary_documents.get("/edit/{id}")
def edit(id:int, db: Session = Depends(get_db)):
    data = ReceivedTributaryDocumentClass(db).get(id)

    return {"message": data}

@received_tributary_documents.get("/download/{id}")
def download(id:int, db: Session = Depends(get_db)):
    data = ReceivedTributaryDocumentClass(db).download(id)

    return {"message": data}

@received_tributary_documents.get("/pay_totals")
def pay_totals(db: Session = Depends(get_db)):
    data = ReceivedTributaryDocumentClass(db).getTotalPerSupplier()

    return {"message": data}
