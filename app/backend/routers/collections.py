from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.collection_class import CollectionClass
from app.backend.schemas import StoreCollection

collections = APIRouter(
    prefix="/collections",
    tags=["Collections"]
)

@collections.get("/")
def index(db: Session = Depends(get_db)):
    data = CollectionClass(db).get()

    return {"message": data}

@collections.post("/store")
def store(store_collection: StoreCollection, db: Session = Depends(get_db)):
    collection_inputs = store_collection.dict()

    data = CollectionClass(db).store(collection_inputs)

    return {"message": data}