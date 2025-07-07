from fastapi import APIRouter, Depends
from app.backend.db.database import get_db, get_db2
from sqlalchemy.orm import Session
from app.backend.classes.collection_class import CollectionClass
from app.backend.schemas import StoreCollection, CollectionList, CollectionSearch, ManualStoreCollection, UpdateCollection
from app.backend.classes.whatsapp_class import WhatsappClass
from app.backend.auth.auth_user import get_current_active_user
from app.backend.schemas import UserLogin

collections = APIRouter(
    prefix="/collections",
    tags=["Collections"]
)

@collections.post("/")
def index(collection: CollectionList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CollectionClass(db).get_all(session_user.rol_id, session_user.rut, collection.branch_office_id, collection.cashier_id, collection.added_date, collection.page)

    return {"message": data}

@collections.post("/detail")
def detail(collection: CollectionList, db: Session = Depends(get_db)):
    data = CollectionClass(db).get_all_with_detail(collection.branch_office_id, collection.cashier_id, collection.added_date, collection.page)

    return {"message": data}

@collections.post("/detail/search")
def detail(collection: CollectionList, db: Session = Depends(get_db)):
    data = CollectionClass(db).get_all_with_detail(collection.branch_office_id, collection.cashier_id, collection.added_date, collection.page)

    return {"message": data}

@collections.post("/store")
def store(store_collection: StoreCollection, db: Session = Depends(get_db)):
    collection_inputs = store_collection.dict()

    data = CollectionClass(db).store(collection_inputs)

    return {"message": data}

@collections.post("/search")
def search(collection_inputs:CollectionSearch, db: Session = Depends(get_db), session_user: UserLogin = Depends(get_current_active_user)):
    data = CollectionClass(db).get_all(session_user.rol_id, session_user.rut, collection_inputs.branch_office_id, collection_inputs.cashier_id, collection_inputs.added_date, collection_inputs.page)

    return {"message": data}

@collections.get("/total_collection/{branch_office_id}/{collection_date}")
def total_collection(branch_office_id:int, collection_date: str, db: Session = Depends(get_db)):
    data = CollectionClass(db).total_collection(branch_office_id, collection_date)

    return {"message": data}

@collections.post("/manual_store")
def manual_store(manual_store_collection: ManualStoreCollection, db: Session = Depends(get_db)):
    collection_inputs = manual_store_collection.dict()

    data = CollectionClass(db).manual_store(collection_inputs)
    return {"message": data}

@collections.delete("/delete/{id}")
def delete(id: int, db: Session = Depends(get_db)):
    CollectionClass(db).delete(id)

    return {"message": "success"}

@collections.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    data = CollectionClass(db).get(id)

    return {"message": data}

@collections.post("/update")
def post(update_collection: UpdateCollection, db: Session = Depends(get_db)):
    data = CollectionClass(db).update(update_collection)

    return {"message": data}

@collections.get("/cron")
def cron(db: Session = Depends(get_db), db2: Session = Depends(get_db2)):
    data = CollectionClass(db2).get_all_collections()

    CollectionClass(db).update_all_collections(data)

    return {"message": 'Updated o inserted collections in the second database.'}