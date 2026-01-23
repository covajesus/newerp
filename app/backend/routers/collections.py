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

@collections.get("/total_collections/{rol_id}")
def total_collections(rol_id:int, db: Session = Depends(get_db)):
    data = CollectionClass(db).total_collections(rol_id)
    return {"message": data}

@collections.delete("/delete/{id}")
def delete(id: int, db: Session = Depends(get_db)):
    CollectionClass(db).delete(id)

    return {"message": "success"}

@collections.get("/update_deposits")
def update_deposits(db: Session = Depends(get_db)):
    CollectionClass(db).update_deposits()

    return {"message": '12121'}

@collections.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    data = CollectionClass(db).get(id)

    return {"message": data}

@collections.post("/update")
def post(update_collection: UpdateCollection, db: Session = Depends(get_db)):
    data = CollectionClass(db).update(update_collection)

    return {"message": data}

@collections.get("/cron")
def cron_default(
    db: Session = Depends(get_db),
    db2: Session = Depends(get_db2)
):
    """
    Endpoint GET para actualizar colecciones desde la segunda base de datos.
    Sin parámetros: trae todas las sucursales y desde 10 días atrás hasta hoy.
    
    Ejemplo de uso:
    GET /collections/cron
    """
    from datetime import date, timedelta
    
    # Valores por defecto: todas las sucursales, últimos 10 días
    branch_office_id_param = None
    since = (date.today() - timedelta(days=10)).strftime('%Y-%m-%d')
    until = date.today().strftime('%Y-%m-%d')
    
    data = CollectionClass(db2).get_all_collections(
        branch_office_id=branch_office_id_param,
        since=since,
        until=until
    )

    CollectionClass(db).update_all_collections(data)

    return {
        "message": "Updated or inserted collections in the second database.",
        "branch_office_id": None,
        "since": since,
        "until": until,
        "records_processed": len(data) if data else 0
    }

@collections.get("/cron/{branch_office_id}/{since}/{until}")
def cron(
    branch_office_id: int,
    since: str,
    until: str,
    db: Session = Depends(get_db),
    db2: Session = Depends(get_db2)
):
    """
    Endpoint GET para actualizar colecciones desde la segunda base de datos.
    
    Parámetros en la URL:
    - branch_office_id: ID de la sucursal (usar 0 para todas las sucursales)
    - since: Fecha desde en formato 'YYYY-MM-DD'
    - until: Fecha hasta en formato 'YYYY-MM-DD'
    
    Ejemplo de uso:
    GET /collections/cron/1/2025-01-01/2025-01-31
    GET /collections/cron/0/2025-01-01/2025-01-31  (0 = todas las sucursales)
    """
    # Convertir branch_office_id = 0 a None para el método
    branch_office_id_param = None if branch_office_id == 0 else branch_office_id
    
    data = CollectionClass(db2).get_all_collections(
        branch_office_id=branch_office_id_param,
        since=since,
        until=until
    )

    CollectionClass(db).update_all_collections(data)

    return {
        "message": "Updated or inserted collections in the second database.",
        "branch_office_id": branch_office_id,
        "since": since,
        "until": until,
        "records_processed": len(data) if data else 0
    }