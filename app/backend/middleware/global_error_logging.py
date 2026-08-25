"""Handlers globales: cualquier excepción HTTP/API se guarda en logs."""
from __future__ import annotations

import traceback
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.backend.classes.log_class import LogClass
from app.backend.classes.process_registry import (
    resolve_crud_action,
    resolve_process_from_path,
)
from app.backend.db.database import SessionLocal


def _safe_log(
    *,
    process_code: str,
    process_name: str,
    message: str,
    level: str,
    path: str,
    method: str,
    status_code: int | None = None,
    user_rut: str | None = None,
    exc: BaseException | None = None,
    detail: str | None = None,
) -> None:
    db = None
    try:
        # Evitar loop si falla el propio endpoint de logs
        if path.startswith("/logs") or path.startswith("/api/logs"):
            return
        db = SessionLocal()
        action = resolve_crud_action(path, method)
        LogClass(db).log(
            process_code,
            message,
            level=level,
            process_name=process_name,
            reference_type="http",
            error_code=str(status_code) if status_code is not None else action,
            detail=detail
            or f"{method} {path}"
            + (f" | action={action}" if action else "")
            + (f" | status={status_code}" if status_code is not None else ""),
            user_rut=user_rut,
            exc=exc,
        )
    except Exception as e:
        print(f"global log failed: {e}")
        if exc:
            print("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    finally:
        if db is not None:
            try:
                db.close()
            except Exception:
                pass


def _user_rut_from_request(request: Request) -> str | None:
    # Si algún middleware setea request.state.user; si no, None
    user = getattr(request.state, "user", None)
    if user is None:
        return None
    return getattr(user, "rut", None) or getattr(user, "username", None)


def register_global_error_logging(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        # 401/404 son comunes: se registran como warning; 5xx como error
        status = int(exc.status_code or 500)
        if status >= 500:
            level = "error"
        elif status in (401, 403, 404):
            level = "warning"
        else:
            level = "warning"

        code, name = resolve_process_from_path(request.url.path)
        _safe_log(
            process_code=code,
            process_name=name,
            message=str(exc.detail) if exc.detail is not None else f"HTTP {status}",
            level=level,
            path=request.url.path,
            method=request.method,
            status_code=status,
            user_rut=_user_rut_from_request(request),
            exc=exc if status >= 500 else None,
        )
        return JSONResponse(status_code=status, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        code, name = resolve_process_from_path(request.url.path)
        _safe_log(
            process_code=code,
            process_name=name,
            message="Error de validación de request",
            level="warning",
            path=request.url.path,
            method=request.method,
            status_code=422,
            user_rut=_user_rut_from_request(request),
            detail=str(exc.errors()),
            exc=exc,
        )
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        code, name = resolve_process_from_path(request.url.path)
        _safe_log(
            process_code=code,
            process_name=name,
            message=str(exc) or exc.__class__.__name__,
            level="error",
            path=request.url.path,
            method=request.method,
            status_code=500,
            user_rut=_user_rut_from_request(request),
            exc=exc,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor", "message": str(exc)},
        )
