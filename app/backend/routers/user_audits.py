from typing import Any, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.backend.auth.auth_user import get_current_active_user
from app.backend.classes.user_audit_class import UserAuditClass
from app.backend.db.database import get_db
from app.backend.schemas import UserLogin

user_audits = APIRouter(prefix="/user_audits", tags=["UserAudits"])


class UserAuditEvent(BaseModel):
    action_type: str = Field(..., min_length=1, max_length=32)
    path: str | None = None
    route_name: str | None = None
    method: str | None = None
    process_code: str | None = None
    element_tag: str | None = None
    element_id: str | None = None
    element_text: str | None = None
    message: str | None = None
    detail: str | None = None
    meta: dict[str, Any] | None = None
    duration_ms: int | None = None
    session_id: str | None = None
    source: str = "frontend"


class UserAuditBatchPayload(BaseModel):
    events: list[UserAuditEvent] = Field(default_factory=list, max_length=100)
    session_id: str | None = None


class UserAuditListPayload(BaseModel):
    page: int = 1
    items_per_page: int = 50
    user_rut: str | None = None
    action_type: str | None = None
    path: str | None = None
    audit_date: str | None = None  # YYYY-MM-DD
    session_id: str | None = None


def _client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    if request.client:
        return (request.client.host or "")[:64]
    return None


@user_audits.post("/batch")
def store_batch(
    payload: UserAuditBatchPayload,
    request: Request,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Recibe lote de eventos UI del frontend."""
    if not payload.events:
        return {"message": {"status": "success", "saved": 0, "errors": 0}}

    result = UserAuditClass(db).record_many(
        [e.model_dump() for e in payload.events],
        defaults={
            "user_rut": getattr(session_user, "rut", None),
            "user_full_name": getattr(session_user, "full_name", None),
            "rol_id": getattr(session_user, "rol_id", None),
            "session_id": payload.session_id,
            "ip_address": _client_ip(request),
            "user_agent": (request.headers.get("user-agent") or "")[:512],
            "source": "frontend",
        },
    )
    return {"message": result}


@user_audits.post("/")
def index(
    payload: UserAuditListPayload,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Listado / filtro de auditoría (por RUT, fecha, acción, etc.)."""
    data = UserAuditClass(db).get_all(
        page=payload.page,
        items_per_page=payload.items_per_page,
        user_rut=payload.user_rut,
        action_type=payload.action_type,
        path=payload.path,
        audit_date=payload.audit_date,
        session_id=payload.session_id,
    )
    return {"message": data}
