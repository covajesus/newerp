"""Middleware: registra llamadas API autenticadas en user_audits."""
from __future__ import annotations

import os
from jose import jwt, JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.backend.classes.user_audit_class import UserAuditClass
from app.backend.db.database import SessionLocal
from app.backend.db.models import UserModel

SKIP_PREFIXES = (
    "/user_audits",
    "/api/user_audits",
    "/logs",
    "/api/logs",
    "/docs",
    "/openapi",
    "/redoc",
    "/favicon",
)


def _should_skip(path: str) -> bool:
    p = path or "/"
    return any(p == pref or p.startswith(pref + "/") for pref in SKIP_PREFIXES)


def _user_from_auth_header(authorization: str | None) -> tuple[str | None, str | None, int | None]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None, None, None
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None, None, None
    try:
        decoded = jwt.decode(
            token,
            os.environ["SECRET_KEY"],
            algorithms=[os.environ.get("ALGORITHM", "HS256")],
        )
        rut = decoded.get("sub")
        if not rut:
            return None, None, None
    except (JWTError, KeyError, Exception):
        return None, None, None

    db = SessionLocal()
    try:
        user = db.query(UserModel).filter(UserModel.rut == rut).first()
        if not user:
            return str(rut), None, None
        return str(user.rut), getattr(user, "full_name", None), getattr(user, "rol_id", None)
    finally:
        db.close()


class UserAuditApiMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path or "/"
        method = (request.method or "GET").upper()

        # Solo mutaciones + POST de listados pesados; GET puros no (mucho ruido)
        track = method in ("POST", "PUT", "PATCH", "DELETE")
        if not track or _should_skip(path):
            return await call_next(request)

        rut, full_name, rol_id = _user_from_auth_header(request.headers.get("authorization"))
        response = await call_next(request)

        if not rut:
            return response

        # No auditar fallos de auth
        if int(getattr(response, "status_code", 0) or 0) in (401, 403):
            return response

        db = None
        try:
            db = SessionLocal()
            forwarded = request.headers.get("x-forwarded-for")
            ip = (
                forwarded.split(",")[0].strip()
                if forwarded
                else (request.client.host if request.client else None)
            )
            UserAuditClass(db).record(
                user_rut=rut,
                user_full_name=full_name,
                rol_id=rol_id,
                action_type="api",
                path=path,
                method=method,
                message=f"{method} {path}",
                detail=f"status={getattr(response, 'status_code', '')}",
                ip_address=ip,
                user_agent=(request.headers.get("user-agent") or "")[:512],
                source="api",
                meta={"status_code": getattr(response, "status_code", None)},
            )
        except Exception as e:
            print(f"user audit api middleware failed: {e}")
        finally:
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass
        return response
