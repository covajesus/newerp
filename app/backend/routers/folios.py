from fastapi import APIRouter, Depends
from app.backend.classes.folio_class import FolioClass
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.db.models import FolioModel
from datetime import datetime

folios = APIRouter(
    prefix="/folios",
    tags=["Folios"]
)

@folios.get("/get/{branch_office_id}/{cashier_id}/{quantity}")
def get(branch_office_id:int, cashier_id:int, quantity:int, db: Session = Depends(get_db)):
    data = FolioClass(db).get(branch_office_id, cashier_id, quantity)

    return {"message": data}

@folios.get("/update/{folio}")
def update(folio:int, db: Session = Depends(get_db)):
    data = FolioClass(db).update(folio)

    return {"message": data}

@folios.get("/caf")
def caf(db: Session = Depends(get_db)):
    # Define el rango de folios
    folio_start = 16981820
    folio_end = 17021050
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