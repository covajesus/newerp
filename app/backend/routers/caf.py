from fastapi import APIRouter, Depends
from app.backend.classes.folio_class import FolioClass
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import CafList

cafs = APIRouter(
    prefix="/cafs",
    tags=["Cafs"]
)

@cafs.post("/")
def get_all(caf: CafList, db: Session = Depends(get_db)):

    data = FolioClass(db).get_all(caf)

    return {"message": data}