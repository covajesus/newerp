from fastapi import APIRouter, Depends
from app.backend.classes.folio_class import FolioClass
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.db.models import FolioModel
from app.backend.schemas import FolioList
from datetime import datetime

folios = APIRouter(
    prefix="/folios",
    tags=["Folios"]
)

@folios.post("/")
def get_all_folios(folio: FolioList, db: Session = Depends(get_db)):

    return {"message": 1}

@folios.get("/get/{branch_office_id}/{cashier_id}/{requested_quantity}/{quantity_in_cashier}")
def get(branch_office_id:int, cashier_id:int, requested_quantity:int, quantity_in_cashier:int, db: Session = Depends(get_db)):
    data = FolioClass(db).get(branch_office_id, cashier_id, requested_quantity, quantity_in_cashier)

    return {"message": ''}

@folios.get("/request/{branch_office_id}/{cashier_id}/{requested_quantity}/{quantity_in_cashier}")
def get(branch_office_id:int, cashier_id:int, requested_quantity:int, quantity_in_cashier:int, db: Session = Depends(get_db)):
    data = FolioClass(db).get(branch_office_id, cashier_id, requested_quantity, quantity_in_cashier)

    return {"message": data}

@folios.get("/data/{branch_office_id}/{cashier_id}/{requested_quantity}/{quantity_in_cashier}")
def get_folios(branch_office_id:int, cashier_id:int, requested_quantity:int, quantity_in_cashier:int, db: Session = Depends(get_db)):
    data = FolioClass(db).get_folio(branch_office_id, cashier_id, requested_quantity, quantity_in_cashier)

    return {"message": '1'}

@folios.get("/update/{folio}")
def update(folio:int, db: Session = Depends(get_db)):
    data = FolioClass(db).update(folio)

    return {"message": data}

@folios.get("/update_billed_ticket/{folio}")
def update(folio:int, db: Session = Depends(get_db)):
    data = FolioClass(db).update_billed_ticket(folio)

    return {"message": data}

@folios.get("/validate")
def validate(db: Session = Depends(get_db)):
    data = FolioClass(db).validate()

    return {"message": f"Validated the quantity of folios"}

@folios.get("/assignation/{folio}/{branch_office_id}/{cashier_id}")
def assignation(folio:int, branch_office_id:int, cashier_id:int, db: Session = Depends(get_db)):
    data = FolioClass(db).assignation(folio, branch_office_id, cashier_id)
    
    return {"message": data}

@folios.get("/validate_1")
def assignation(db: Session = Depends(get_db)):
    data = FolioClass(db).a()
    
    return {"message": "1"}

@folios.get("/get_from_caf")
def get_from_caf(db: Session = Depends(get_db)):
    # Define el rango de folios
    folio_start = 17141051
    folio_end = 17341050
    current_date = datetime.now().strftime('%Y-%m-%d')

    # Iterar sobre el rango y realizar la inserción para cada folio
    for folio_number in range(folio_start, folio_end + 1):
        folio = FolioModel()
        folio.folio = folio_number
        folio.branch_office_id = 0
        folio.cashier_id = 0
        folio.requested_status_id = 0
        folio.used_status_id = 0
        folio.added_date = current_date
        folio.updated_date = current_date

        db.add(folio)

        # Confirmar todos los cambios después del bucle
        db.commit()

    return {"message": f"Inserted folios from {folio_start} to {folio_end}"}

@folios.get("/report")
def report(db: Session = Depends(get_db)):
    data = FolioClass(db).report()
    
    return {"message": data}

@folios.get("/get_quantity_per_cashier")
def report(db: Session = Depends(get_db)):
    data = FolioClass(db).get_quantity_per_cashier()
    
    return {"message": data}