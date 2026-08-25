from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.backend.auth.auth_user import get_current_active_user
from app.backend.classes.log_class import LogClass
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
