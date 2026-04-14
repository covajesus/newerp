from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from app.backend.classes.folio_class import FolioClass
from app.backend.db.database import get_db, get_db2
from sqlalchemy.orm import Session
from app.backend.db.models import FolioModel
from app.backend.schemas import FolioList, FolioDb2Store
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

@folios.get("/quantity/{cashier_id}/{quantity}")
def quantity(cashier_id: int, quantity: int, db: Session = Depends(get_db)):
    data = FolioClass(db).quantity(cashier_id, quantity)

    return {"message": data}


@folios.get("/db2/counts_by_segment")
def counts_by_segment_db2(db2: Session = Depends(get_db2)):
    """
    Totales en DB2 por folio_segment_id (solo tabla folios en DB2; sin depender de `segments`).
    Cuenta filas con branch_office_id = 0 y requested_status_id = 0; si el segmento tiene folios
    pero ninguno cumple el filtro, total = 0.
    """
    query = text("""
        SELECT
            seg.folio_segment_id,
            COALESCE(SUM(
                CASE
                    WHEN f.branch_office_id = 0 AND f.requested_status_id = 0 THEN 1
                    ELSE 0
                END
            ), 0) AS total
        FROM (
            SELECT DISTINCT folio_segment_id
            FROM folios
            WHERE folio_segment_id IS NOT NULL
        ) seg
        LEFT JOIN folios f ON f.folio_segment_id = seg.folio_segment_id
        GROUP BY seg.folio_segment_id
        ORDER BY seg.folio_segment_id
    """)
    result = db2.execute(query)
    rows = [
        {"folio_segment_id": row.folio_segment_id, "total": int(row.total)}
        for row in result
    ]
    return {"message": rows}


_MAX_FOLIOS_DB2_STORE = 100_000


@folios.post("/db2/store")
def store_folios_db2(body: FolioDb2Store, db2: Session = Depends(get_db2)):
    """
    Inserta en DB2 (tabla folios) un registro por cada número entre `start_folio` y `end_folio` (inclusive).
    `folio` = número del rango; `folio_segment_id` = el enviado; branch_office_id, cashier_id,
    requested_status_id, used_status_id y billed_status_id en 0.
    """
    if body.folio_segment_id is None:
        raise HTTPException(status_code=400, detail="Seleccione un segmento")
    if body.start_folio > body.end_folio:
        raise HTTPException(status_code=400, detail="start_folio no puede ser mayor que end_folio")
    count = body.end_folio - body.start_folio + 1
    if count > _MAX_FOLIOS_DB2_STORE:
        raise HTTPException(
            status_code=400,
            detail=f"El rango supera el máximo permitido ({_MAX_FOLIOS_DB2_STORE} folios por solicitud)",
        )
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    insert_sql = text("""
        INSERT INTO folios (
            folio, branch_office_id, cashier_id, folio_segment_id,
            requested_status_id, used_status_id, billed_status_id,
            added_date, updated_date
        ) VALUES (
            :folio, 0, 0, :folio_segment_id,
            0, 0, 0,
            :added_date, :updated_date
        )
    """)
    try:
        for folio_number in range(body.start_folio, body.end_folio + 1):
            db2.execute(
                insert_sql,
                {
                    "folio": folio_number,
                    "folio_segment_id": body.folio_segment_id,
                    "added_date": now,
                    "updated_date": now,
                },
            )
        db2.commit()
    except Exception as e:
        db2.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {
        "message": "OK",
        "inserted": count,
        "start_folio": body.start_folio,
        "end_folio": body.end_folio,
        "folio_segment_id": body.folio_segment_id,
    }