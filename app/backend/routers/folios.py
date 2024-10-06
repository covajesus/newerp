from fastapi import APIRouter, Depends
from app.backend.classes.folio_class import FolioClass
from app.backend.db.database import get_db
from sqlalchemy.orm import Session

folios = APIRouter(
    prefix="/folios",
    tags=["Folios"]
)

@folios.get("/get/{branch_office_id}/{cashier_id}/{quantity}")
def get(branch_office_id:int, cashier_id:int, quantity:int, db: Session = Depends(get_db)):
    data = FolioClass(db).get(branch_office_id, cashier_id, quantity)

    return {"message": data}