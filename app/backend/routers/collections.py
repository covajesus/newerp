from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.collection_class import CollectionClass

collections = APIRouter(
    prefix="/collections",
    tags=["Collections"]
)

@collections.get("/")
def index(db: Session = Depends(get_db)):
    data = CollectionClass(db).get()

    return {"message": data}