from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.collection_class import CollectionClass
from app.backend.schemas import StoreCollection, CollectionList, CollectionSearch

collections = APIRouter(
    prefix="/collections",
    tags=["Collections"]
)

@collections.post("/")
def index(collection: CollectionList, db: Session = Depends(get_db)):
    data = CollectionClass(db).get_all(collection.branch_office_id, collection.cashier_id, collection.added_date, collection.page)

    return {"message": data}

@collections.post("/store")
def store(store_collection: StoreCollection, db: Session = Depends(get_db)):
    collection_inputs = store_collection.dict()

    data = CollectionClass(db).store(collection_inputs)

    return {"message": data}

@collections.post("/search")
def search(collection_inputs:CollectionSearch, db: Session = Depends(get_db)):
    data = CollectionClass(db).get_all(collection_inputs.branch_office_id, collection_inputs.cashier_id, collection_inputs.added_date, collection_inputs.page)

    return {"message": data}

@collections.get("/total_collection/{branch_office_id}/{collection_date}")
def total_collection(branch_office_id:int, collection_date: str, db: Session = Depends(get_db)):
    data = CollectionClass(db).total_collection(branch_office_id, collection_date)

    return {"message": data}