"""
API pull-based para cajas: consultan comandos y reportan resultado.
Header opcional: Authorization: Bearer <CASHIER_SYNC_API_TOKEN>
"""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.backend.db.database import get_db
from app.backend.classes.cashier_sync_command_class import (
    complete_command,
    get_next_pending_command,
    verify_sync_token,
)

cashier_sync_router = APIRouter(prefix="/cashier_sync", tags=["Cashier sync (pull)"])


class CompleteSyncBody(BaseModel):
    status: str  # completado | error
    resultado: Optional[str] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None


def _check_token(authorization: Optional[str] = Header(None)):
    if not verify_sync_token(authorization):
        raise HTTPException(status_code=401, detail="Token inválido")


@cashier_sync_router.get("/{cashier_id}/next")
def get_next_command(
    cashier_id: int,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """
    La caja llama periódicamente (ej. cada 5–10 s). Si hay trabajo pendiente, pasa a ejecutando y lo devuelve.
    """
    _check_token(authorization)
    cmd = get_next_pending_command(db, cashier_id)
    if not cmd:
        return {"command": None}
    return {"command": cmd}


@cashier_sync_router.post("/{cashier_id}/commands/{command_id}/complete")
def post_complete(
    cashier_id: int,
    command_id: int,
    body: CompleteSyncBody,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """
    La caja ejecuta el script y reporta. cashier_id debe coincidir con el comando.
    """
    _check_token(authorization)
    if body.status not in ("completado", "error"):
        raise HTTPException(status_code=400, detail="status debe ser completado o error")
    res = complete_command(
        db,
        command_id,
        cashier_id,
        body.status,
        body.resultado,
        body.error,
        body.duration_ms,
    )
    if not res.get("ok"):
        raise HTTPException(status_code=404, detail=res.get("message", "Error"))
    return res
