from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, date
from typing import Optional, Any
import requests

from app.backend.db.models import (
    SettingModel,
    AccountingAccountModel,
    AccountingEntryModel,
    AccountingEntryLineModel,
    AccountingEntryDocumentModel,
    UserModel,
)

LIBREDTE_ASIENTO_URL = "https://libredte.cl/api/lce/lce_asientos/crear/76063822"
LIBREDTE_DEFAULT_TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
ACCOUNTING_BACKEND_LIBREDTE = 1
ACCOUNTING_BACKEND_BOTH = 2


class AccountingEntryClass:
    def __init__(self, db: Session):
        self.db = db

    def get_backend(self) -> int:
        row = (
            self.db.query(SettingModel.accounting_backend)
            .filter(SettingModel.id == 1)
            .first()
        )
        if not row:
            return ACCOUNTING_BACKEND_LIBREDTE
        try:
            value = int(row[0] if not hasattr(row, "accounting_backend") else row.accounting_backend)
        except (TypeError, ValueError, IndexError):
            return ACCOUNTING_BACKEND_LIBREDTE
        if value == ACCOUNTING_BACKEND_BOTH:
            return ACCOUNTING_BACKEND_BOTH
        return ACCOUNTING_BACKEND_LIBREDTE

    def create(
        self,
        payload: dict,
        token: Optional[str] = None,
        user_id: Optional[int] = None,
        source: str = "system",
    ) -> dict:
        """
        Create accounting entry.
        backend 1: LibreDTE only
        backend 2: LibreDTE + local Intrajis tables
        """
        backend = self.get_backend()
        result = {
            "status": "success",
            "backend": backend,
            "libredte": None,
            "local": None,
            "errors": [],
        }

        libredte_result = self._create_libredte(payload, token or LIBREDTE_DEFAULT_TOKEN)
        result["libredte"] = libredte_result
        if libredte_result.get("status") != "success":
            result["status"] = "error"
            result["errors"].append(libredte_result.get("message") or "LibreDTE error")
            return result

        if backend == ACCOUNTING_BACKEND_BOTH:
            try:
                local_result = self._create_local(payload, user_id=user_id, source=source)
                result["local"] = local_result
                if local_result.get("status") != "success":
                    result["status"] = "partial"
                    result["errors"].append(local_result.get("message") or "Local persist error")
            except Exception as exc:
                self.db.rollback()
                result["status"] = "partial"
                result["local"] = {"status": "error", "message": str(exc)}
                result["errors"].append(str(exc))
                print(f"[accounting_entry.create] local error after LibreDTE OK: {exc}", flush=True)

        return result

    def _create_libredte(self, payload: dict, token: str) -> dict:
        try:
            response = requests.post(
                LIBREDTE_ASIENTO_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )
            if response.status_code == 200:
                return {"status": "success", "http_status": 200, "body": _safe_json(response)}
            return {
                "status": "error",
                "http_status": response.status_code,
                "message": f"LibreDTE HTTP {response.status_code}: {(response.text or '')[:300]}",
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def _parse_entry_date(self, value: Any) -> date:
        text = str(value or "").strip()[:10]
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return datetime.now().date()

    def _next_number(self, year: int) -> int:
        current = (
            self.db.query(func.max(AccountingEntryModel.number))
            .filter(extract("year", AccountingEntryModel.entry_date) == year)
            .scalar()
        )
        return int(current or 0) + 1

    def _create_local(
        self,
        payload: dict,
        user_id: Optional[int] = None,
        source: str = "system",
    ) -> dict:
        entry_date = self._parse_entry_date(payload.get("fecha"))
        glosa = str(payload.get("glosa") or "").strip()
        if not glosa:
            return {"status": "error", "message": "glosa is required"}

        detalle = payload.get("detalle") or {}
        debe = detalle.get("debe") or {}
        haber = detalle.get("haber") or {}
        if not isinstance(debe, dict) or not isinstance(haber, dict):
            return {"status": "error", "message": "detalle.debe/haber must be objects"}

        lines = []
        total_debe = 0
        total_haber = 0
        sort_order = 0
        for account_code, amount in debe.items():
            amt = int(round(float(amount or 0)))
            if amt == 0:
                continue
            lines.append(
                {
                    "account_code": str(account_code).strip(),
                    "debit": abs(amt),
                    "credit": 0,
                    "sort_order": sort_order,
                }
            )
            total_debe += abs(amt)
            sort_order += 1
        for account_code, amount in haber.items():
            amt = int(round(float(amount or 0)))
            if amt == 0:
                continue
            lines.append(
                {
                    "account_code": str(account_code).strip(),
                    "debit": 0,
                    "credit": abs(amt),
                    "sort_order": sort_order,
                }
            )
            total_haber += abs(amt)
            sort_order += 1

        if not lines:
            return {"status": "error", "message": "No accounting lines"}
        if total_debe != total_haber:
            return {
                "status": "error",
                "message": f"Unbalanced entry debe={total_debe} haber={total_haber}",
            }

        now = datetime.now()
        number = self._next_number(entry_date.year)
        period = entry_date.strftime("%Y-%m")
        operation = payload.get("operacion")
        if operation not in (None, "", "I", "E"):
            operation = str(operation)[:8]

        entry = AccountingEntryModel(
            number=number,
            period=period,
            entry_date=entry_date,
            glosa=glosa[:512],
            operation=operation or None,
            annulled=0,
            user_id=user_id,
            source=source or "system",
            added_date=now,
            updated_date=now,
        )
        self.db.add(entry)
        self.db.flush()

        for line in lines:
            self.db.add(
                AccountingEntryLineModel(
                    accounting_entry_id=entry.id,
                    account_code=line["account_code"][:32],
                    debit=line["debit"],
                    credit=line["credit"],
                    concept=None,
                    sort_order=line["sort_order"],
                )
            )

        documentos = payload.get("documentos") or {}
        for doc_type_key, doc_type in (("emitidos", "emitido"), ("recibidos", "recibido")):
            for doc in documentos.get(doc_type_key) or []:
                if not isinstance(doc, dict):
                    continue
                try:
                    folio = int(doc.get("folio") or 0)
                except (TypeError, ValueError):
                    folio = 0
                try:
                    dte_type_id = int(doc.get("dte") or 0) or None
                except (TypeError, ValueError):
                    dte_type_id = None
                self.db.add(
                    AccountingEntryDocumentModel(
                        accounting_entry_id=entry.id,
                        doc_type=doc_type,
                        issuer_rut=str(doc.get("rut") or doc.get("issuer_rut") or "") or None,
                        dte_type_id=dte_type_id,
                        folio=folio or None,
                        period=period,
                    )
                )

        self.db.commit()
        return {
            "status": "success",
            "id": entry.id,
            "number": entry.number,
            "period": entry.period,
        }

    def store_manual(self, form_data, user_id: Optional[int] = None) -> dict:
        """UI create form → LibreDTE payload → create()."""
        lines = getattr(form_data, "lines", None) or []
        debe = {}
        haber = {}
        for line in lines:
            code = str(getattr(line, "account_code", None) or line.get("account_code") or "").strip()
            if not code:
                continue
            debit = int(getattr(line, "debit", None) if not isinstance(line, dict) else line.get("debit") or 0)
            credit = int(getattr(line, "credit", None) if not isinstance(line, dict) else line.get("credit") or 0)
            if debit:
                debe[code] = int(debe.get(code, 0)) + abs(debit)
            if credit:
                haber[code] = int(haber.get(code, 0)) + abs(credit)

        docs_emitidos = []
        docs_recibidos = []
        for doc in getattr(form_data, "documents", None) or []:
            get = (lambda k, d=doc: getattr(d, k, None) if not isinstance(d, dict) else d.get(k))
            item = {
                "dte": get("dte_type_id") or 0,
                "folio": get("folio") or 0,
                "rut": get("issuer_rut") or "",
            }
            doc_type = str(get("doc_type") or "emitido").lower()
            if doc_type.startswith("recib"):
                docs_recibidos.append(item)
            else:
                docs_emitidos.append(item)

        payload = {
            "fecha": str(getattr(form_data, "entry_date", None) or datetime.now().date()),
            "glosa": str(getattr(form_data, "glosa", "") or "").strip(),
            "detalle": {"debe": debe, "haber": haber},
            "operacion": getattr(form_data, "operation", None) or None,
            "documentos": {
                "emitidos": docs_emitidos,
                "recibidos": docs_recibidos,
            },
        }
        return self.create(payload, user_id=user_id, source="manual")

    def search(
        self,
        period=None,
        number=None,
        since=None,
        until=None,
        glosa=None,
        annulled=None,
        user_id=None,
        page=1,
        items_per_page=20,
    ):
        query = self.db.query(AccountingEntryModel)
        if period:
            query = query.filter(AccountingEntryModel.period.like(f"{period}%"))
        if number not in (None, ""):
            try:
                query = query.filter(AccountingEntryModel.number == int(number))
            except (TypeError, ValueError):
                pass
        if since:
            query = query.filter(AccountingEntryModel.entry_date >= since)
        if until:
            query = query.filter(AccountingEntryModel.entry_date <= until)
        if glosa:
            query = query.filter(AccountingEntryModel.glosa.ilike(f"%{glosa}%"))
        if annulled not in (None, ""):
            query = query.filter(AccountingEntryModel.annulled == int(annulled))
        if user_id not in (None, ""):
            query = query.filter(AccountingEntryModel.user_id == int(user_id))

        total_items = query.count()
        page = max(1, int(page or 1))
        items_per_page = max(1, int(items_per_page or 20))
        total_pages = (total_items + items_per_page - 1) // items_per_page if total_items else 0
        rows = (
            query.order_by(AccountingEntryModel.id.desc())
            .offset((page - 1) * items_per_page)
            .limit(items_per_page)
            .all()
        )

        user_ids = {r.user_id for r in rows if r.user_id}
        users = {}
        if user_ids:
            for u in self.db.query(UserModel.id, UserModel.full_name).filter(UserModel.id.in_(user_ids)).all():
                users[u.id] = u.full_name

        data = [
            {
                "id": r.id,
                "number": r.number,
                "period": r.period,
                "entry_date": r.entry_date.strftime("%Y-%m-%d") if r.entry_date else None,
                "glosa": r.glosa,
                "operation": r.operation,
                "annulled": int(r.annulled or 0),
                "user_id": r.user_id,
                "user": users.get(r.user_id),
                "source": r.source,
            }
            for r in rows
        ]
        return {
            "data": data,
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page,
            "items_per_page": items_per_page,
        }

    def get(self, entry_id: int):
        entry = self.db.query(AccountingEntryModel).filter(AccountingEntryModel.id == entry_id).first()
        if not entry:
            return {"status": "error", "message": "Asiento no encontrado"}
        lines = (
            self.db.query(AccountingEntryLineModel)
            .filter(AccountingEntryLineModel.accounting_entry_id == entry.id)
            .order_by(AccountingEntryLineModel.sort_order.asc())
            .all()
        )
        docs = (
            self.db.query(AccountingEntryDocumentModel)
            .filter(AccountingEntryDocumentModel.accounting_entry_id == entry.id)
            .all()
        )
        return {
            "status": "success",
            "data": {
                "id": entry.id,
                "number": entry.number,
                "period": entry.period,
                "entry_date": entry.entry_date.strftime("%Y-%m-%d") if entry.entry_date else None,
                "glosa": entry.glosa,
                "operation": entry.operation,
                "annulled": int(entry.annulled or 0),
                "user_id": entry.user_id,
                "source": entry.source,
                "lines": [
                    {
                        "id": l.id,
                        "account_code": l.account_code,
                        "debit": l.debit,
                        "credit": l.credit,
                        "concept": l.concept,
                    }
                    for l in lines
                ],
                "documents": [
                    {
                        "id": d.id,
                        "doc_type": d.doc_type,
                        "issuer_rut": d.issuer_rut,
                        "dte_type_id": d.dte_type_id,
                        "folio": d.folio,
                        "period": d.period,
                    }
                    for d in docs
                ],
            },
        }

    def annul(self, entry_id: int):
        entry = self.db.query(AccountingEntryModel).filter(AccountingEntryModel.id == entry_id).first()
        if not entry:
            return {"status": "error", "message": "Asiento no encontrado"}
        entry.annulled = 1
        entry.updated_date = datetime.now()
        self.db.commit()
        return {"status": "success", "id": entry.id}

    def sync_local_annul_after_libredte_delete(
        self,
        number=None,
        glosa=None,
        year=None,
    ):
        """
        When accounting_backend=2, also annul matching local entries after a LibreDTE delete.
        """
        if self.get_backend() != ACCOUNTING_BACKEND_BOTH:
            return {"status": "skipped", "reason": "backend_libredte_only"}

        query = self.db.query(AccountingEntryModel).filter(AccountingEntryModel.annulled == 0)
        if number not in (None, ""):
            try:
                query = query.filter(AccountingEntryModel.number == int(number))
            except (TypeError, ValueError):
                pass
        if year not in (None, ""):
            try:
                query = query.filter(extract("year", AccountingEntryModel.entry_date) == int(year))
            except (TypeError, ValueError):
                pass
        if glosa:
            query = query.filter(AccountingEntryModel.glosa.ilike(f"%{str(glosa).strip()}%"))

        rows = query.all()
        if not rows and glosa:
            # fallback: try by glosa alone
            rows = (
                self.db.query(AccountingEntryModel)
                .filter(
                    AccountingEntryModel.annulled == 0,
                    AccountingEntryModel.glosa.ilike(f"%{str(glosa).strip()}%"),
                )
                .all()
            )

        now = datetime.now()
        for row in rows:
            row.annulled = 1
            row.updated_date = now
        if rows:
            self.db.commit()
        return {"status": "success", "annulled": len(rows)}

    def list_accounts(self, active_only=True):
        query = self.db.query(AccountingAccountModel)
        if active_only:
            query = query.filter(AccountingAccountModel.status_id == 1)
        rows = query.order_by(AccountingAccountModel.code.asc()).all()
        return [
            {"id": r.id, "code": r.code, "name": r.name, "status_id": r.status_id}
            for r in rows
        ]

    def store_account(self, code: str, name: str):
        code = str(code or "").strip()
        name = str(name or "").strip()
        if not code or not name:
            return {"status": "error", "message": "code and name required"}
        exists = (
            self.db.query(AccountingAccountModel.id)
            .filter(AccountingAccountModel.code == code)
            .first()
        )
        if exists:
            return {"status": "error", "message": "Account code already exists"}
        now = datetime.now()
        row = AccountingAccountModel(
            code=code,
            name=name,
            status_id=1,
            added_date=now,
            updated_date=now,
        )
        self.db.add(row)
        self.db.commit()
        return {"status": "success", "id": row.id, "code": row.code}


def _safe_json(response):
    try:
        return response.json()
    except Exception:
        return (response.text or "")[:500]
