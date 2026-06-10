import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import bindparam, text
from app.backend.classes.folio_class import FolioClass
from app.backend.classes.whatsapp_class import WhatsappClass
from app.backend.db.database import get_db, get_db2
from sqlalchemy.orm import Session
from app.backend.db.models import FolioModel, CashierModel
from app.backend.schemas import FolioList, FolioDb2Store, UserLogin
from app.backend.auth.auth_user import get_current_active_user
from datetime import datetime


def _parse_csv_folio_numbers_semicolon(content: str) -> set[int]:
    """CSV con separador `;`, columna folio en índice 2: id;used_id;folio;..."""
    folios: set[int] = set()
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(";")]
        if len(parts) < 3:
            continue
        if parts[0].lower() == "id" and parts[2].lower() == "folio":
            continue
        try:
            folios.add(int(parts[2]))
        except ValueError:
            continue
    return folios

folios = APIRouter(
    prefix="/folios",
    tags=["Folios"]
)

@folios.get("/reserve/{document_type_id}")
def reserve_folio_by_document_type(
    document_type_id: int,
    branch_office_id: int,
    dte_id: int | None = None,
    db: Session = Depends(get_db),
):
    """
    Reserva folio de la pool central (branch_office_id=0, used_id=0).
    document_type_id en URL: 33 factura, 39 boleta, 61 nota de crédito.
    Query: branch_office_id (requerido), dte_id (opcional).
    """
    data = FolioClass(db).reserve_next_by_document_type(
        document_type_id,
        branch_office_id=branch_office_id,
        dte_id=dte_id,
    )
    return {"message": data}


@folios.get("/release/{folio_row_id}")
def release_folio_pool(folio_row_id: int, db: Session = Depends(get_db)):
    """Libera folio reservado (used_id=0) si la emisión no se completó."""
    data = FolioClass(db).release_folio_pool(folio_row_id)
    return {"message": data}


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


@folios.api_route("/db2/cron_check_low_stock", methods=["GET", "POST"])
def cron_check_low_stock(
    db: Session = Depends(get_db),
    db2: Session = Depends(get_db2),
):
    """
    Cron: si el stock disponible por segmento (misma lógica que /db2/counts_by_segment)
    cae bajo FOLIO_LOW_STOCK_THRESHOLD (default 100_000), envía WhatsApp (destinatarios en
    WhatsappClass.send_folio_low_stock_alerts) con plantilla whatsapp_templates.id=7. Sin token: restringir en firewall/nginx.
    """
    threshold = int(os.getenv("FOLIO_LOW_STOCK_THRESHOLD", "100000"))

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
        {"folio_segment_id": m["folio_segment_id"], "total": int(m["total"])}
        for m in result.mappings().all()
    ]

    alerts = []
    for r in rows:
        sid = r["folio_segment_id"]
        tot = r["total"]
        if sid is None or tot >= threshold:
            continue
        outs = WhatsappClass(db).send_folio_low_stock_alerts(int(sid), tot)
        alerts.append({"folio_segment_id": int(sid), "available": tot, "whatsapp": outs})

    return {
        "message": {
            "threshold": threshold,
            "segments_checked": rows,
            "segments_alerted": [a["folio_segment_id"] for a in alerts],
            "detail": alerts,
        }
    }


@folios.get("/db2/segment_detail/{folio_segment_id}")
def segment_detail_db2(folio_segment_id: int, db2: Session = Depends(get_db2)):
    """
    Folios asignados a cajas en DB2, agrupados por día (fecha de asignación) y por caja.
    Solo filas con caja asignada y estado solicitado distinto de «disponible en central».
    """
    query = text("""
        SELECT
            DATE(COALESCE(f.updated_date, f.added_date)) AS request_day,
            f.cashier_id,
            COUNT(*) AS folios_count
        FROM folios f
        WHERE f.folio_segment_id = :seg
          AND f.cashier_id IS NOT NULL
          AND f.cashier_id > 0
          AND COALESCE(f.requested_status_id, 0) <> 0
        GROUP BY DATE(COALESCE(f.updated_date, f.added_date)), f.cashier_id
        ORDER BY request_day DESC, f.cashier_id ASC
    """)
    result = db2.execute(query, {"seg": folio_segment_id})
    rows = []
    for row in result.mappings():
        rd = row.get("request_day")
        if hasattr(rd, "isoformat"):
            day_str = rd.isoformat()
        else:
            day_str = str(rd)[:10]
        rows.append(
            {
                "request_day": day_str,
                "cashier_id": int(row["cashier_id"]),
                "folios_count": int(row["folios_count"]),
            }
        )
    return {"message": rows}


@folios.get("/db2/segment_group_folios/{folio_segment_id}")
def segment_group_folios_db2(
    folio_segment_id: int,
    request_day: str,
    cashier_id: int,
    db2: Session = Depends(get_db2),
):
    """
    Folios DB2 de un grupo concreto (misma fecha de asignación, segmento y caja que `segment_detail`).
    Devuelve número de folio y estados solicitado / utilizado / facturado.
    """
    query = text("""
        SELECT
            f.folio,
            f.branch_office_id,
            f.cashier_id,
            COALESCE(f.requested_status_id, 0) AS requested_status_id,
            COALESCE(f.used_status_id, 0) AS used_status_id,
            COALESCE(f.billed_status_id, 0) AS billed_status_id
        FROM folios f
        WHERE f.folio_segment_id = :seg
          AND f.cashier_id = :cashier_id
          AND f.cashier_id IS NOT NULL
          AND f.cashier_id > 0
          AND COALESCE(f.requested_status_id, 0) <> 0
          AND DATE(COALESCE(f.updated_date, f.added_date)) = CAST(:request_day AS DATE)
        ORDER BY f.folio ASC
    """)
    result = db2.execute(
        query,
        {"seg": folio_segment_id, "cashier_id": cashier_id, "request_day": request_day},
    )
    rows = []
    for row in result.mappings():
        bo = row.get("branch_office_id")
        rows.append(
            {
                "folio": int(row["folio"]),
                "branch_office_id": int(bo) if bo is not None else None,
                "cashier_id": int(row["cashier_id"]),
                "requested_status_id": int(row["requested_status_id"]),
                "used_status_id": int(row["used_status_id"]),
                "billed_status_id": int(row["billed_status_id"]),
            }
        )
    return {"message": rows}


@folios.get("/db2/cashiers_for_segment/{folio_segment_id}")
def cashiers_for_segment(
    folio_segment_id: int,
    db: Session = Depends(get_db),
    _session_user: UserLogin = Depends(get_current_active_user),
):
    """Cajas (datos maestros) cuyo folio_segment_id coincide con el segmento de la ruta."""
    rows = (
        db.query(CashierModel)
        .filter(CashierModel.folio_segment_id == folio_segment_id)
        .order_by(CashierModel.cashier)
        .all()
    )
    data = [
        {
            "id": r.id,
            "cashier": r.cashier or "",
            "branch_office_id": r.branch_office_id,
        }
        for r in rows
    ]
    return {"message": data}


@folios.post("/db2/release_folios_csv/{folio_segment_id}")
async def release_folios_csv(
    folio_segment_id: int,
    cashier_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    db2: Session = Depends(get_db2),
    _session_user: UserLogin = Depends(get_current_active_user),
):
    """
    Libera en DB2 solo para la caja indicada: pone en 0 branch_office_id, cashier_id y estados,
    para todo folio que siga asignado a esa caja y cuyo número de folio NO aparezca en el CSV.
    """
    if folio_segment_id not in (1, 2, 3):
        raise HTTPException(status_code=400, detail="Segmento debe ser 1, 2 o 3")

    cashier = db.query(CashierModel).filter(CashierModel.id == cashier_id).first()
    if not cashier:
        raise HTTPException(status_code=400, detail="Caja no encontrada")
    if cashier.folio_segment_id is None or int(cashier.folio_segment_id) != folio_segment_id:
        raise HTTPException(status_code=400, detail="La caja no pertenece a este segmento")

    raw = await file.read()
    if len(raw) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Archivo demasiado grande (máx. 15 MB)")
    try:
        text_body = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text_body = raw.decode("latin-1")

    csv_folios = _parse_csv_folio_numbers_semicolon(text_body)
    if not csv_folios:
        raise HTTPException(
            status_code=400,
            detail="No se leyeron folios válidos del CSV (formato id;used_id;folio;...)",
        )

    result = db2.execute(
        text("""
            SELECT id, folio FROM folios
            WHERE folio_segment_id = :seg
              AND cashier_id = :cid
        """),
        {"seg": folio_segment_id, "cid": cashier_id},
    )
    assigned = result.mappings().all()

    to_release_ids: list[int] = []
    for row in assigned:
        rid = row.get("id")
        fno = row.get("folio")
        if rid is None or fno is None:
            continue
        try:
            fid = int(rid)
            fn = int(fno)
        except (TypeError, ValueError):
            continue
        if fn not in csv_folios:
            to_release_ids.append(fid)

    if not to_release_ids:
        return {
            "message": {
                "released": 0,
                "csv_folio_count": len(csv_folios),
                "assigned_rows_for_cashier": len(assigned),
                "detail": "Ningún folio asignado a esta caja quedó fuera del CSV.",
            }
        }

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    chunk_size = 2000
    total_u = 0
    for i in range(0, len(to_release_ids), chunk_size):
        chunk = to_release_ids[i : i + chunk_size]
        upd = (
            text("""
            UPDATE folios
            SET branch_office_id = 0,
                cashier_id = 0,
                requested_status_id = 0,
                used_status_id = 0,
                billed_status_id = 0,
                updated_date = :updated_date
            WHERE id IN :ids
              AND folio_segment_id = :seg
              AND cashier_id = :cid
            """)
            .bindparams(bindparam("ids", expanding=True))
        )
        r = db2.execute(
            upd,
            {
                "ids": chunk,
                "updated_date": now,
                "seg": folio_segment_id,
                "cid": cashier_id,
            },
        )
        total_u += r.rowcount if r.rowcount is not None else len(chunk)

    db2.commit()
    return {
        "message": {
            "released": len(to_release_ids),
            "csv_folio_count": len(csv_folios),
            "assigned_rows_for_cashier_before": len(assigned),
            "updated_rows": total_u,
        }
    }


@folios.post("/db2/store")
def store_folios_db2(body: FolioDb2Store, db2: Session = Depends(get_db2)):
    """
    Inserta en DB2 (tabla folios) por:
    - rango explícito (`start_folio` + `end_folio`), o
    - `quantity` (calcula correlativo desde MAX(folio) del segmento + 1).
    """
    if body.folio_segment_id is None:
        raise HTTPException(status_code=400, detail="Seleccione un segmento")
    if body.quantity is not None:
        if body.quantity <= 0:
            raise HTTPException(status_code=400, detail="quantity debe ser mayor que 0")
        max_folio_q = text("""
            SELECT COALESCE(MAX(folio), 0) AS max_folio
            FROM folios
            WHERE folio_segment_id = :seg
        """)
        max_row = db2.execute(max_folio_q, {"seg": body.folio_segment_id}).mappings().first()
        max_folio = int(max_row["max_folio"]) if max_row and max_row.get("max_folio") is not None else 0
        start_folio = max_folio + 1
        end_folio = max_folio + int(body.quantity)
    else:
        if body.start_folio is None or body.end_folio is None:
            raise HTTPException(status_code=400, detail="Debe enviar start_folio y end_folio, o quantity")
        if body.start_folio > body.end_folio:
            raise HTTPException(status_code=400, detail="start_folio no puede ser mayor que end_folio")
        start_folio = int(body.start_folio)
        end_folio = int(body.end_folio)
    count = end_folio - start_folio + 1
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
        for folio_number in range(start_folio, end_folio + 1):
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
        "start_folio": start_folio,
        "end_folio": end_folio,
        "folio_segment_id": body.folio_segment_id,
    }