"""
Cola pull-based: las cajas consultan comandos pendientes y reportan resultado.
Notificaciones por WhatsApp al administrador que solicitó la sync.
"""
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import pytz
from sqlalchemy.orm import Session

from app.backend.classes.whatsapp_class import WhatsappClass
from app.backend.db.models import BranchOfficeModel, CashierModel, CashierSyncCommandModel

_TZ = pytz.timezone("America/Santiago")

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

    now = datetime.now(_TZ)
    row.completed_at = now
    row.result_text = result_text
    row.error_text = error_text
    row.duration_ms = duration_ms
    row.status = "completado" if final_status == "completado" else "error"

    db.commit()

    # Notificar por WhatsApp al solicitante
    wa = row.requester_wa_id
    if wa:
        try:
            if row.status == "completado":
                body = (
                    f"✅ *Caja {cashier_id}* sincronizada correctamente.\n"
                    f"Comando #{command_id}"
                )
                if duration_ms is not None:
                    body += f"\n⏱ Duración: {duration_ms} ms"
                if result_text:
                    body += f"\n_{result_text[:500]}_"
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

    return {"ok": True, "command_id": command_id, "status": row.status}


def verify_sync_token(token_header: Optional[str]) -> bool:
    secret = os.getenv("CASHIER_SYNC_API_TOKEN", "")
    if not secret:
        return True  # sin token configurado, no bloquear (solo desarrollo)
    if not token_header:
        return False
    if token_header.startswith("Bearer "):
        token_header = token_header[7:].strip()
    return token_header == secret
