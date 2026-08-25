"""Registro de logs de errores/eventos por proceso."""
from __future__ import annotations

import traceback
from datetime import datetime
from typing import Any, Optional

from app.backend.db.models import LogModel, ProcessModel


class LogClass:
    def __init__(self, db):
        self.db = db

    def get_or_create_process(
        self,
        code: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ProcessModel:
        row = self.db.query(ProcessModel).filter(ProcessModel.code == code).first()
        if row:
            return row
        now = datetime.now()
        row = ProcessModel(
            code=code,
            name=name or code,
            description=description,
            status_id=1,
            added_date=now,
            updated_date=now,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def log(
        self,
        process_code: str,
        message: str,
        *,
        level: str = "error",
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        user_rut: Optional[str] = None,
        error_code: Optional[str] = None,
        detail: Optional[Any] = None,
        exc: Optional[BaseException] = None,
        process_name: Optional[str] = None,
    ) -> dict:
        """Guarda un registro en logs con día/hora detallados."""
        try:
            process = self.get_or_create_process(process_code, name=process_name)
            now = datetime.now()
            detail_text = None
            if detail is not None:
                detail_text = detail if isinstance(detail, str) else str(detail)
            stack = None
            if exc is not None:
                stack = "".join(
                    traceback.format_exception(type(exc), exc, exc.__traceback__)
                )
                if not detail_text:
                    detail_text = str(exc)

            row = LogModel(
                process_id=int(process.id),
                level=(level or "error").lower()[:16],
                reference_type=reference_type,
                reference_id=int(reference_id) if reference_id is not None else None,
                user_rut=str(user_rut)[:32] if user_rut else None,
                error_code=str(error_code)[:64] if error_code else None,
                message=str(message or "Error")[:65000],
                detail=detail_text,
                stack_trace=stack,
                log_datetime=now,
                log_date=now.date(),
                log_time=now.strftime("%H:%M:%S"),
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

            result = {
                "status": "success",
                "id": row.id,
                "process_id": process.id,
                "log_datetime": now.isoformat(sep=" ", timespec="seconds"),
            }

            # Cada error también se notifica a Slack (#intrajis_errors)
            if (row.level or "").lower() == "error":
                try:
                    from app.backend.classes.slack_notifier import send_error_to_slack

                    slack_result = send_error_to_slack(
                        process_name=process.name or process_code,
                        process_code=process.code or process_code,
                        message=row.message,
                        log_id=row.id,
                        level=row.level,
                        log_datetime=result["log_datetime"],
                        reference_type=row.reference_type,
                        reference_id=row.reference_id,
                        user_rut=row.user_rut,
                        error_code=row.error_code,
                        detail=row.detail,
                    )
                    result["slack"] = slack_result
                except Exception as slack_exc:
                    print(f"Slack notify from LogClass failed: {slack_exc}")
                    result["slack"] = {"status": "error", "message": str(slack_exc)}

            return result
        except Exception as e:
            try:
                self.db.rollback()
            except Exception:
                pass
            print(f"LogClass.log failed: {e}")
            return {"status": "error", "message": str(e)}

    def log_error(self, process_code: str, message: str, **kwargs) -> dict:
        kwargs.setdefault("level", "error")
        return self.log(process_code, message, **kwargs)

    def get_all(
        self,
        page: int = 1,
        items_per_page: int = 50,
        process_code: Optional[str] = None,
        level: Optional[str] = None,
        log_date: Optional[str] = None,
    ) -> dict | str:
        try:
            q = (
                self.db.query(LogModel, ProcessModel)
                .outerjoin(ProcessModel, ProcessModel.id == LogModel.process_id)
                .order_by(LogModel.id.desc())
            )
            if process_code:
                q = q.filter(ProcessModel.code == process_code)
            if level:
                q = q.filter(LogModel.level == level.lower())
            if log_date:
                q = q.filter(LogModel.log_date == log_date)

            total_items = q.count()
            rows = (
                q.offset((page - 1) * items_per_page)
                .limit(items_per_page)
                .all()
            )
            total_pages = (total_items + items_per_page - 1) // items_per_page or 1
            data = []
            for log, process in rows:
                data.append(
                    {
                        "id": log.id,
                        "process_id": log.process_id,
                        "process_code": process.code if process else None,
                        "process_name": process.name if process else None,
                        "level": log.level,
                        "reference_type": log.reference_type,
                        "reference_id": log.reference_id,
                        "user_rut": log.user_rut,
                        "error_code": log.error_code,
                        "message": log.message,
                        "detail": log.detail,
                        "stack_trace": log.stack_trace,
                        "log_datetime": str(log.log_datetime) if log.log_datetime else None,
                        "log_date": str(log.log_date) if log.log_date else None,
                        "log_time": log.log_time,
                        "year": log.year,
                        "month": log.month,
                        "day": log.day,
                        "hour": log.hour,
                        "minute": log.minute,
                        "second": log.second,
                        "weekday": log.weekday,
                    }
                )
            return {
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "items_per_page": items_per_page,
                "data": data,
            }
        except Exception as e:
            return f"Error: {e}"
