"""Auditoría de actividad por usuario."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from app.backend.classes.log_class import LogClass
from app.backend.classes.process_registry import (
    resolve_process_from_frontend_path,
    resolve_process_from_path,
)
from app.backend.db.models import ProcessModel, UserAuditModel


class UserAuditClass:
    def __init__(self, db):
        self.db = db

    def _resolve_process_id(
        self,
        *,
        process_code: Optional[str],
        path: Optional[str],
        source: str = "frontend",
    ) -> Optional[int]:
        code = process_code
        name = None
        if not code and path:
            if source == "api":
                code, name = resolve_process_from_path(path)
            else:
                code, name = resolve_process_from_frontend_path(path)
        if not code:
            code, name = "user_audit", "Auditoría de usuarios"
        process = LogClass(self.db).get_or_create_process(code, name=name or code)
        return int(process.id) if process else None

    def record(
        self,
        *,
        user_rut: str,
        action_type: str,
        user_full_name: Optional[str] = None,
        rol_id: Optional[int] = None,
        session_id: Optional[str] = None,
        process_code: Optional[str] = None,
        path: Optional[str] = None,
        route_name: Optional[str] = None,
        method: Optional[str] = None,
        element_tag: Optional[str] = None,
        element_id: Optional[str] = None,
        element_text: Optional[str] = None,
        message: Optional[str] = None,
        detail: Optional[str] = None,
        meta: Optional[Any] = None,
        duration_ms: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        source: str = "frontend",
    ) -> dict:
        now = datetime.now()
        process_id = self._resolve_process_id(
            process_code=process_code, path=path, source=source
        )
        meta_json = None
        if meta is not None:
            meta_json = meta if isinstance(meta, str) else json.dumps(meta, ensure_ascii=False, default=str)

        row = UserAuditModel(
            user_rut=str(user_rut)[:32],
            user_full_name=(str(user_full_name)[:255] if user_full_name else None),
            rol_id=int(rol_id) if rol_id is not None else None,
            session_id=(str(session_id)[:64] if session_id else None),
            process_id=process_id,
            action_type=str(action_type or "unknown")[:32],
            path=(str(path)[:512] if path else None),
            route_name=(str(route_name)[:128] if route_name else None),
            method=(str(method)[:16] if method else None),
            element_tag=(str(element_tag)[:64] if element_tag else None),
            element_id=(str(element_id)[:128] if element_id else None),
            element_text=(str(element_text)[:512] if element_text else None),
            message=(str(message)[:1024] if message else None),
            detail=detail,
            meta_json=meta_json,
            duration_ms=int(duration_ms) if duration_ms is not None else None,
            ip_address=(str(ip_address)[:64] if ip_address else None),
            user_agent=(str(user_agent)[:512] if user_agent else None),
            audit_datetime=now,
            audit_date=now.date(),
            audit_time=now.strftime("%H:%M:%S"),
            year=now.year,
            month=now.month,
            day=now.day,
            hour=now.hour,
            minute=now.minute,
            second=now.second,
            weekday=now.weekday(),
            added_date=now,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"status": "success", "id": row.id}

    def record_many(self, events: list[dict], *, defaults: Optional[dict] = None) -> dict:
        defaults = defaults or {}
        saved = 0
        errors = 0
        for ev in events:
            try:
                payload = {**defaults, **(ev or {})}
                user_rut = payload.get("user_rut") or defaults.get("user_rut")
                if not user_rut:
                    errors += 1
                    continue
                self.record(
                    user_rut=str(user_rut),
                    action_type=str(payload.get("action_type") or "unknown"),
                    user_full_name=payload.get("user_full_name") or defaults.get("user_full_name"),
                    rol_id=payload.get("rol_id") if payload.get("rol_id") is not None else defaults.get("rol_id"),
                    session_id=payload.get("session_id") or defaults.get("session_id"),
                    process_code=payload.get("process_code"),
                    path=payload.get("path"),
                    route_name=payload.get("route_name"),
                    method=payload.get("method"),
                    element_tag=payload.get("element_tag"),
                    element_id=payload.get("element_id"),
                    element_text=payload.get("element_text"),
                    message=payload.get("message"),
                    detail=payload.get("detail"),
                    meta=payload.get("meta"),
                    duration_ms=payload.get("duration_ms"),
                    ip_address=payload.get("ip_address") or defaults.get("ip_address"),
                    user_agent=payload.get("user_agent") or defaults.get("user_agent"),
                    source=str(payload.get("source") or "frontend"),
                )
                saved += 1
            except Exception:
                self.db.rollback()
                errors += 1
        return {"status": "success", "saved": saved, "errors": errors}

    def get_all(
        self,
        *,
        page: int = 1,
        items_per_page: int = 50,
        user_rut: Optional[str] = None,
        action_type: Optional[str] = None,
        path: Optional[str] = None,
        audit_date: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict:
        page = max(1, int(page or 1))
        items_per_page = min(200, max(1, int(items_per_page or 50)))
        q = self.db.query(UserAuditModel, ProcessModel.code, ProcessModel.name).outerjoin(
            ProcessModel, ProcessModel.id == UserAuditModel.process_id
        )
        if user_rut:
            q = q.filter(UserAuditModel.user_rut == str(user_rut))
        if action_type:
            q = q.filter(UserAuditModel.action_type == str(action_type))
        if path:
            q = q.filter(UserAuditModel.path.like(f"%{path}%"))
        if audit_date:
            q = q.filter(UserAuditModel.audit_date == audit_date)
        if session_id:
            q = q.filter(UserAuditModel.session_id == str(session_id))

        total = q.count()
        rows = (
            q.order_by(UserAuditModel.audit_datetime.desc())
            .offset((page - 1) * items_per_page)
            .limit(items_per_page)
            .all()
        )
        items = []
        for row, process_code, process_name in rows:
            items.append(
                {
                    "id": row.id,
                    "user_rut": row.user_rut,
                    "user_full_name": row.user_full_name,
                    "rol_id": row.rol_id,
                    "session_id": row.session_id,
                    "process_id": row.process_id,
                    "process_code": process_code,
                    "process_name": process_name,
                    "action_type": row.action_type,
                    "path": row.path,
                    "route_name": row.route_name,
                    "method": row.method,
                    "element_tag": row.element_tag,
                    "element_id": row.element_id,
                    "element_text": row.element_text,
                    "message": row.message,
                    "detail": row.detail,
                    "meta_json": row.meta_json,
                    "duration_ms": row.duration_ms,
                    "ip_address": row.ip_address,
                    "audit_datetime": row.audit_datetime.isoformat(sep=" ", timespec="seconds")
                    if row.audit_datetime
                    else None,
                    "audit_date": str(row.audit_date) if row.audit_date else None,
                    "audit_time": row.audit_time,
                }
            )
        return {
            "items": items,
            "total": total,
            "page": page,
            "items_per_page": items_per_page,
        }
