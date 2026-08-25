from typing import Any, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.backend.auth.auth_user import get_current_active_user
from app.backend.classes.log_class import LogClass
from app.backend.classes.process_registry import resolve_process_from_frontend_path
from app.backend.db.database import get_db
from app.backend.db.models import ProcessModel
from app.backend.schemas import UserLogin

logs = APIRouter(prefix="/logs", tags=["Logs"])


class LogsListPayload(BaseModel):
    page: int = 1
    items_per_page: int = 50
    process_code: str | None = None
    level: str | None = None
    log_date: str | None = None  # YYYY-MM-DD


class ClientLogPayload(BaseModel):
    message: str = Field(..., min_length=1)
    detail: str | None = None
    stack_trace: str | None = None
    level: str = "error"
    source: str | None = None  # console | runtime | promise | vue | axios
    path: str | None = None  # ruta SPA
    process_code: str | None = None
    error_code: str | None = None
    meta: dict[str, Any] | None = None


@logs.post("/")
def index(
    payload: LogsListPayload,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = LogClass(db).get_all(
        page=payload.page,
        items_per_page=payload.items_per_page,
        process_code=payload.process_code,
        level=payload.level,
        log_date=payload.log_date,
    )
    return {"message": data}


@logs.get("/processes")
def list_processes(
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    rows = db.query(ProcessModel).order_by(ProcessModel.name).all()
    return {
        "message": [
            {
                "id": r.id,
                "code": r.code,
                "name": r.name,
                "description": r.description,
                "status_id": r.status_id,
            }
            for r in rows
        ]
    }


@logs.post("/client")
def client_log(
    payload: ClientLogPayload,
    request: Request,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Recibe errores del frontend (console/runtime) → logs + Slack."""
    source = (payload.source or "frontend").lower()
    source_to_process = {
        "console": ("frontend_console", "Frontend - Console"),
        "runtime": ("frontend_runtime", "Frontend - Runtime"),
        "promise": ("frontend_promise", "Frontend - Promise"),
        "vue": ("frontend_vue", "Frontend - Vue"),
        "axios": ("frontend_axios", "Frontend - Axios"),
    }

    # Preferir módulo de la pantalla (path SPA); si no, proceso por tipo de error
    if payload.process_code:
        process_code = payload.process_code
        process_name = payload.process_code
    elif payload.path:
        process_code, process_name = resolve_process_from_frontend_path(payload.path)
    else:
        process_code, process_name = source_to_process.get(
            source, ("frontend", "Frontend - General")
        )

    detail_parts = []
    if payload.detail:
        detail_parts.append(payload.detail)
    if payload.path:
        detail_parts.append(f"path={payload.path}")
    if payload.source:
        detail_parts.append(f"source={payload.source}")
    if payload.meta:
        detail_parts.append(f"meta={payload.meta}")
    ua = request.headers.get("user-agent")
    if ua:
        detail_parts.append(f"ua={ua[:300]}")

    result = LogClass(db).log(
        process_code,
        payload.message,
        level=(payload.level or "error").lower(),
        process_name=process_name,
        reference_type="frontend",
        user_rut=getattr(session_user, "rut", None),
        error_code=(payload.error_code or source)[:64],
        detail=" | ".join(detail_parts) if detail_parts else None,
        stack_trace=payload.stack_trace,
    )
    return {"message": result}
