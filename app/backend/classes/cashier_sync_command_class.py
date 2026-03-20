"""
Cola pull-based: las cajas consultan comandos pendientes y reportan resultado.
Notificaciones por WhatsApp al administrador que solicitó la sync.
"""
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytz
from sqlalchemy.orm import Session

from app.backend.classes.collection_class import sync_collections_from_db2_to_main
from app.backend.classes.whatsapp_class import WhatsappClass
from app.backend.db.database import SessionLocalDB2
from app.backend.db.models import CashierModel, CashierSyncCommandModel, CollectionModel

_TZ = pytz.timezone("America/Santiago")


def _post_sync_collections_refresh(db: Session, branch_office_id: int, cashier_id: int) -> str:
    """
    Tras subir ventas desde la caja: ejecuta el mismo flujo que GET /collections/cron
    (DB2 → collections en ERP) para esa sucursal y devuelve texto para WhatsApp/result_text.
    """
    if os.getenv("CASHIER_SYNC_SKIP_COLLECTIONS_CRON", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "si",
    ):
        return "⏭ Refresco collections omitido (CASHIER_SYNC_SKIP_COLLECTIONS_CRON)."

    if SessionLocalDB2 is None:
        return (
            "⚠️ *Refresco ERP* no ejecutado: DB2 no configurada (.env).\n"
            "Cuando suba ventas, ejecute el cron: GET /api/collections/cron/{sucursal}/{desde}/{hasta}"
        )

    today = datetime.now(_TZ).date()
    since = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    until = today.strftime("%Y-%m-%d")

    db2 = SessionLocalDB2()
    try:
        res = sync_collections_from_db2_to_main(
            db,
            db2,
            branch_office_id,
            since,
            until,
        )
        if res.get("ok"):
            lines = [
                f"📥 *Cron collections* (DB2→ERP): {res['records_processed']} filas "
                f"({res['since']} … {res['until']}, sucursal {branch_office_id})."
            ]
        else:
            lines = [f"⚠️ Cron collections falló: {res.get('error', '?')}"]
    finally:
        db2.close()

    db.expire_all()
    snap = (
        db.query(CollectionModel)
        .filter(
            CollectionModel.branch_office_id == branch_office_id,
            CollectionModel.cashier_id == cashier_id,
            CollectionModel.added_date == today,
        )
        .first()
    )
    if snap:
        lines.append(
            f"📊 *Collections hoy* (caja {cashier_id}): tickets={snap.total_tickets}, "
            f"efectivo=${snap.cash_gross_amount or 0}, tarjeta=${snap.card_gross_amount or 0}"
        )
    else:
        lines.append(
            f"📊 *Collections hoy*: sin fila para caja {cashier_id} en fecha {until} "
            "(revisar que la caja haya subido a DB2 o la fecha del movimiento)."
        )
    return "\n".join(lines)


# Mismos filtros que CashierClass.get_list (cajas operativas)
_SYNC_FILTERS = (
    CashierModel.folio_segment_id != 9,
    CashierModel.folio_segment_id != 8,
    CashierModel.folio_segment_id != 0,
)


def get_syncable_cashiers(db: Session, branch_office_id: int) -> List[CashierModel]:
    return (
        db.query(CashierModel)
        .filter(CashierModel.branch_office_id == branch_office_id)
        .filter(*_SYNC_FILTERS)
        .order_by(CashierModel.id)
        .all()
    )


def create_sync_commands(
    db: Session,
    branch_office_id: int,
    requester_wa_id: str,
    scope_all: bool,
    single_cashier_id: Optional[int],
) -> Dict[str, Any]:
    """
    Crea filas pendientes. scope_all=True: una fila por cada caja activa.
    scope_all=False: una fila para single_cashier_id (debe pertenecer a la sucursal).
    """
    batch_id = str(uuid.uuid4())
    now = datetime.now(_TZ)
    cashiers = get_syncable_cashiers(db, branch_office_id)
    if not cashiers:
        return {"ok": False, "message": "No hay cajas activas para esta sucursal."}

    to_create: List[CashierModel] = []
    if scope_all:
        to_create = list(cashiers)
    else:
        c = next((x for x in cashiers if x.id == single_cashier_id), None)
        if not c:
            return {"ok": False, "message": "ID de caja no válido o no pertenece a la sucursal."}
        to_create = [c]

    created_ids = []
    for c in to_create:
        row = CashierSyncCommandModel(
            branch_office_id=branch_office_id,
            cashier_id=c.id,
            batch_id=batch_id,
            status="pendiente",
            requester_wa_id=requester_wa_id,
            action="sync_sales",
            created_at=now,
        )
        db.add(row)
        db.flush()
        created_ids.append((row.id, c.id, c.cashier or ""))

    db.commit()
    return {"ok": True, "batch_id": batch_id, "created": created_ids}


def get_next_pending_command(db: Session, cashier_id: int) -> Optional[Dict[str, Any]]:
    """La caja toma el comando más antiguo pendiente y pasa a ejecutando."""
    row = (
        db.query(CashierSyncCommandModel)
        .filter(
            CashierSyncCommandModel.cashier_id == cashier_id,
            CashierSyncCommandModel.status == "pendiente",
        )
        .order_by(CashierSyncCommandModel.id.asc())
        .first()
    )
    if not row:
        return None
    now = datetime.now(_TZ)
    row.status = "ejecutando"
    row.started_at = now
    db.commit()
    db.refresh(row)
    return {
        "command_id": row.id,
        "action": row.action or "sync_sales",
        "batch_id": row.batch_id,
        "branch_office_id": row.branch_office_id,
        "cashier_id": row.cashier_id,
    }


def complete_command(
    db: Session,
    command_id: int,
    cashier_id: int,
    final_status: str,
    result_text: Optional[str],
    error_text: Optional[str],
    duration_ms: Optional[int],
) -> Dict[str, Any]:
    """completado | error"""
    row = (
        db.query(CashierSyncCommandModel)
        .filter(
            CashierSyncCommandModel.id == command_id,
            CashierSyncCommandModel.cashier_id == cashier_id,
        )
        .first()
    )
    if not row:
        return {"ok": False, "message": "Comando no encontrado"}

    if row.status not in ("pendiente", "ejecutando"):
        return {"ok": False, "message": "Comando ya finalizado"}

    st = (final_status or "").strip().lower()
    if st not in ("completado", "error"):
        st = "error"

    now = datetime.now(_TZ)
    row.completed_at = now
    row.error_text = error_text
    row.duration_ms = duration_ms
    row.status = "completado" if st == "completado" else "error"

    if row.status == "completado":
        verify_block = _post_sync_collections_refresh(db, row.branch_office_id, cashier_id)
        base = (result_text or "").strip()
        row.result_text = (base + "\n---\n" if base else "") + verify_block
    else:
        row.result_text = result_text

    db.commit()
    # Tras commit, refrescar fila para que status/result_text coincidan con BD (evita status stale "ejecutando").
    db.refresh(row)

    # Notificar solo al número que creó la orden (requester_wa_id en la fila del comando).
    # Si eliges *TODAS* las cajas, recibirás un mensaje por cada caja al terminar (siempre a tu número).
    wa = (row.requester_wa_id or "").strip()
    notify = os.getenv("CASHIER_SYNC_NOTIFY_COMPLETION", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )
    if wa and notify:
        try:
            print(
                f"[cashier_sync] WhatsApp fin de sync → wa_id={wa} "
                f"command_id={command_id} cashier_id={cashier_id} status={row.status}"
            )
            if row.status == "completado":
                body = (
                    f"✅ *Caja {cashier_id}* sincronizada correctamente.\n"
                    f"Comando #{command_id}"
                )
                if duration_ms is not None:
                    body += f"\n⏱ Duración: {duration_ms} ms"
                if row.result_text:
                    body += f"\n{row.result_text[:1200]}"
            else:
                body = (
                    f"❌ *Caja {cashier_id}* error al sincronizar.\n"
                    f"Comando #{command_id}"
                )
                if duration_ms is not None:
                    body += f"\n⏱ Duración: {duration_ms} ms"
                if error_text:
                    body += f"\n{error_text[:500]}"
            WhatsappClass(db).send_text_message(wa, body)
        except Exception as e:
            print(f"[cashier_sync] notify whatsapp: {e}")

    return {
        "ok": True,
        "command_id": command_id,
        "status": str(row.status or ""),
        "result_text": row.result_text,
    }


def verify_sync_token(token_header: Optional[str]) -> bool:
    secret = os.getenv("CASHIER_SYNC_API_TOKEN", "")
    if not secret:
        return True  # sin token configurado, no bloquear (solo desarrollo)
    if not token_header:
        return False
    if token_header.startswith("Bearer "):
        token_header = token_header[7:].strip()
    return token_header == secret
