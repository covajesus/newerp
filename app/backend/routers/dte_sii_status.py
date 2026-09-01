from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.backend.auth.auth_user import get_current_active_user
from app.backend.classes.dte_sii_status_class import DteSiiStatusClass
from app.backend.db.database import get_db
from app.backend.schemas import UserLogin

dte_sii_status = APIRouter(prefix="/dte_sii_status", tags=["DTE SII Status"])


class SyncBatchPayload(BaseModel):
    lookback_days: int | None = Field(default=None, ge=1, le=365)
    limit: int = Field(default=2000, ge=1, le=5000)
    max_seconds: int | None = Field(default=None, ge=30, le=900)


@dte_sii_status.post("/sync")
def sync_batch(
    payload: SyncBatchPayload | None = None,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Sincroniza estados SII (SimpleFactura documentsIssued) de DTE emitidos."""
    del session_user
    body = payload or SyncBatchPayload()
    data = DteSiiStatusClass(db).sync(
        lookback_days=body.lookback_days,
        limit=body.limit,
        max_seconds=body.max_seconds,
    )
    return {"message": data}


@dte_sii_status.post("/sync/{dte_id}")
def sync_one(
    dte_id: int,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    del session_user
    data = DteSiiStatusClass(db).sync_one(dte_id)
    return {"message": data}


@dte_sii_status.get("/cron")
def cron_sync(
    db: Session = Depends(get_db),
    lookback_days: int = Query(30, ge=1, le=365),
    limit: int = Query(150, ge=1, le=5000),
    max_seconds: int = Query(90, ge=30, le=900),
    dte_id: int | None = Query(None, ge=1),
):
    """Cron: GET /api/dte_sii_status/cron?lookback_days=30&limit=150&max_seconds=90

    Consulta SimpleFactura día a día. Si has_more=true, repetir (o dejar crontab).
    Prueba 1 DTE: ?dte_id=123
    """
    svc = DteSiiStatusClass(db)
    if dte_id:
        data = svc.sync_one(int(dte_id))
    else:
        data = svc.sync(
            lookback_days=lookback_days,
            limit=limit,
            max_seconds=max_seconds,
        )
    return {"message": data}
