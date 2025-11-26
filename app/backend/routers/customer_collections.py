from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import CustomerCollection
from app.backend.classes.customer_collection_class import CustomerCollectionClass

customer_collections = APIRouter(
    prefix="/customer_collections",
    tags=["CustomerCollections"]
)

@customer_collections.post("/collect")
def store(customer_collection:CustomerCollection, db: Session = Depends(get_db)):
    data = CustomerCollectionClass(db).store(customer_collection)

    return {"message": data}
