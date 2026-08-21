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
    DteModel,
    UserModel,
)

LIBREDTE_ASIENTO_URL = "https://libredte.cl/api/lce/lce_asientos/crear/76063822"
LIBREDTE_ASIENTO_DELETE_URL = "https://libredte.cl/api/lce/lce_asientos/eliminar"
LIBREDTE_COMPANY_RUT = "76063822"
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
        return {"status": "success", "data": self._serialize_entry(entry)}

    def find_by_dte(self, dte_id: int):
        """Local accounting entry linked to an emitted DTE (folio + type, or glosa fallback)."""
        dte = self.db.query(DteModel).filter(DteModel.id == int(dte_id)).first()
        if not dte:
            return {"status": "error", "message": "DTE no encontrado"}

        folio = int(dte.folio or 0)
        dte_type_id = int(dte.dte_type_id or 0)
        entry = None

        if folio > 0 and dte_type_id > 0:
            doc = (
                self.db.query(AccountingEntryDocumentModel)
                .filter(
                    AccountingEntryDocumentModel.doc_type == "emitido",
                    AccountingEntryDocumentModel.folio == folio,
                    AccountingEntryDocumentModel.dte_type_id == dte_type_id,
                )
                .order_by(AccountingEntryDocumentModel.id.desc())
                .first()
            )
            if doc:
                entry = (
                    self.db.query(AccountingEntryModel)
                    .filter(AccountingEntryModel.id == doc.accounting_entry_id)
                    .first()
                )

        if entry is None and folio > 0:
            # Glosa from create_account_asset: ..._{dte.id}_{folio}
            needle = f"_{dte.id}_{folio}"
            entry = (
                self.db.query(AccountingEntryModel)
                .filter(AccountingEntryModel.glosa.ilike(f"%{needle}%"))
                .order_by(AccountingEntryModel.id.desc())
                .first()
            )
        if entry is None and folio > 0:
            entry = (
                self.db.query(AccountingEntryModel)
                .filter(AccountingEntryModel.glosa.ilike(f"%_{folio}%"))
                .order_by(AccountingEntryModel.id.desc())
                .first()
            )

        if not entry:
            return {
                "status": "error",
                "message": "No hay asiento contable local para este documento. "
                "Se crea al marcar el pago (Imputada Pagada) con backend Intrajis activo.",
                "dte_id": dte.id,
                "folio": folio,
                "dte_type_id": dte_type_id,
            }

        return {"status": "success", "data": self._serialize_entry(entry)}

    def _serialize_entry(self, entry: AccountingEntryModel) -> dict:
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
        }

    def _entry_year_number(self, entry: AccountingEntryModel) -> tuple[int, int]:
        year = None
        if entry.entry_date:
            year = int(entry.entry_date.year)
        elif entry.period:
            try:
                year = int(str(entry.period).split("-")[0])
            except (TypeError, ValueError, IndexError):
                year = None
        if year is None:
            year = datetime.now().year
        return year, int(entry.number or 0)

    def annul_local(self, entry_id: int):
        """Marca el asiento como anulado solo en Intrajis."""
        entry = self.db.query(AccountingEntryModel).filter(AccountingEntryModel.id == entry_id).first()
        if not entry:
            return {"status": "error", "message": "Asiento no encontrado"}
        if int(entry.annulled or 0) == 1:
            year, number = self._entry_year_number(entry)
            return {
                "status": "success",
                "id": entry.id,
                "number": number,
                "year": year,
                "message": "El asiento ya estaba anulado en Intrajis",
            }

        year, number = self._entry_year_number(entry)
        entry.annulled = 1
        entry.updated_date = datetime.now()
        self.db.commit()
        return {
            "status": "success",
            "id": entry.id,
            "number": number,
            "year": year,
            "message": "Asiento anulado en Intrajis",
        }

    def annul_libredte(self, entry_id: int):
        """Elimina el asiento equivalente en LibreDTE."""
        entry = self.db.query(AccountingEntryModel).filter(AccountingEntryModel.id == entry_id).first()
        if not entry:
            return {"status": "error", "message": "Asiento no encontrado"}

        year, number = self._entry_year_number(entry)
        libredte_result = self._delete_libredte(
            year=year,
            number=number,
            external_ref=entry.external_ref,
        )
        return {
            "status": libredte_result.get("status") or "error",
            "id": entry.id,
            "number": number,
            "year": year,
            "libredte": libredte_result,
            "message": (
                "Asiento eliminado en LibreDTE"
                if libredte_result.get("status") == "success"
                else (libredte_result.get("message") or "No se pudo eliminar en LibreDTE")
            ),
        }

    def annul(self, entry_id: int):
        """Anula en Intrajis y elimina el asiento equivalente en LibreDTE."""
        local = self.annul_local(entry_id)
        if local.get("status") == "error":
            return local

        libredte = self.annul_libredte(entry_id)
        status = "success"
        if libredte.get("status") == "error":
            status = "partial"

        return {
            "status": status,
            "id": local.get("id"),
            "number": local.get("number"),
            "year": local.get("year"),
            "local": {"status": "success", "annulled": 1},
            "libredte": libredte.get("libredte") or libredte,
            "message": (
                "Asiento anulado en Intrajis y eliminado en LibreDTE"
                if status == "success"
                else (
                    "Asiento anulado en Intrajis, pero no se pudo eliminar en LibreDTE: "
                    f"{libredte.get('message') or 'error desconocido'}"
                )
            ),
        }

    def _delete_libredte(
        self,
        year: int,
        number: int,
        external_ref: Optional[str] = None,
        token: Optional[str] = None,
    ) -> dict:
        auth = token or LIBREDTE_DEFAULT_TOKEN
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {auth}",
        }
        attempts = []
        if year and number:
            attempts.append(
                f"{LIBREDTE_ASIENTO_DELETE_URL}/{int(year)}/{int(number)}/{LIBREDTE_COMPANY_RUT}"
            )
        if external_ref:
            ref = str(external_ref).strip()
            if ref.isdigit():
                attempts.append(f"{LIBREDTE_ASIENTO_DELETE_URL}/{ref}/{LIBREDTE_COMPANY_RUT}")
            # Some imports store "year-number"
            if "-" in ref:
                parts = ref.split("-")
                if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                    attempts.append(
                        f"{LIBREDTE_ASIENTO_DELETE_URL}/{parts[0]}/{parts[1]}/{LIBREDTE_COMPANY_RUT}"
                    )

        if not attempts:
            return {
                "status": "error",
                "message": "Falta año/número del asiento para eliminar en LibreDTE",
            }

        last_error = None
        for url in attempts:
            try:
                print(f"[accounting_entry.annul] LibreDTE DELETE GET {url}", flush=True)
                response = requests.get(url, headers=headers, timeout=60)
                body = (response.text or "")[:400]
                print(
                    f"[accounting_entry.annul] LibreDTE HTTP {response.status_code}: {body}",
                    flush=True,
                )
                if response.status_code == 200:
                    return {
                        "status": "success",
                        "http_status": 200,
                        "url": url,
                        "body": _safe_json(response),
                    }
                # Already deleted / not found → treat as ok for sync
                low = body.lower()
                if response.status_code in (404, 400) and (
                    "no existe" in low
                    or "no se encuentra" in low
                    or "not found" in low
                    or "eliminad" in low
                ):
                    return {
                        "status": "success",
                        "http_status": response.status_code,
                        "url": url,
                        "message": "Asiento no encontrado en LibreDTE (ya eliminado)",
                    }
                last_error = f"LibreDTE HTTP {response.status_code}: {body}"
            except Exception as exc:
                last_error = str(exc)
                print(f"[accounting_entry.annul] LibreDTE error: {exc}", flush=True)

        return {"status": "error", "message": last_error or "No se pudo eliminar en LibreDTE"}

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

    def import_libredte_plan(self, since: str, until: str) -> dict:
        since = str(since or "").strip()[:10]
        until = str(until or "").strip()[:10]
        if not since or not until:
            return {"status": "error", "message": "Desde y hasta son obligatorios", "days": []}
        try:
            start = datetime.strptime(since, "%Y-%m-%d").date()
            end = datetime.strptime(until, "%Y-%m-%d").date()
        except ValueError:
            return {"status": "error", "message": "Fechas inválidas (YYYY-MM-DD)", "days": []}
        if start > end:
            return {"status": "error", "message": "Desde no puede ser mayor que hasta", "days": []}

        days = []
        cursor = start
        while cursor <= end:
            days.append(cursor.strftime("%Y-%m-%d"))
            cursor = cursor.fromordinal(cursor.toordinal() + 1)
        return {
            "status": "success",
            "since": since,
            "until": until,
            "days": days,
            "total_days": len(days),
        }

    def import_from_libredte_day(self, day: str, user_id: Optional[int] = None) -> dict:
        day = str(day or "").strip()[:10]
        if not day:
            return {"status": "error", "message": "El día es obligatorio"}
        return self.import_from_libredte(since=day, until=day, user_id=user_id)

    def import_from_libredte(self, since: str, until: str, user_id: Optional[int] = None) -> dict:
        """
        Fetch LibreDTE asientos between since/until and upsert into local tables.
        Dedupes by external_ref (LibreDTE id / year-number).
        Returns `items` so the UI can show live progress per asiento.
        """
        since = str(since or "").strip()[:10]
        until = str(until or "").strip()[:10]
        if not since or not until:
            return {"status": "error", "message": "Desde y hasta son obligatorios"}

        payload = {
            "periodo": "",
            "fecha_desde": since,
            "fecha_hasta": until,
            "glosa": "",
            "operacion": "",
            "cuenta": "",
            "debe": "",
            "debe_desde": "",
            "debe_hasta": "",
            "haber": "",
            "haber_desde": "",
            "haber_hasta": "",
        }
        try:
            response = requests.post(
                "https://libredte.cl/api/lce/lce_asientos/buscar/76063822",
                json=payload,
                headers={
                    "Authorization": f"Bearer {LIBREDTE_DEFAULT_TOKEN}",
                    "Content-Type": "application/json",
                },
                timeout=90,
            )
        except Exception as exc:
            return {"status": "error", "message": f"Error de conexión LibreDTE: {exc}"}

        if response.status_code != 200:
            return {
                "status": "error",
                "message": f"LibreDTE HTTP {response.status_code}: {(response.text or '')[:300]}",
            }

        try:
            entries = response.json()
        except Exception:
            return {"status": "error", "message": "Respuesta LibreDTE inválida"}

        if not isinstance(entries, list):
            return {"status": "error", "message": "LibreDTE no devolvió una lista de asientos"}

        imported = 0
        skipped = 0
        errors = 0
        now = datetime.now()
        items = []

        for raw in entries:
            if not isinstance(raw, dict):
                errors += 1
                items.append({"action": "error", "message": "Asiento inválido"})
                continue
            try:
                external_ref = self._libredte_external_ref(raw)
                if not external_ref:
                    errors += 1
                    items.append(
                        {
                            "action": "error",
                            "glosa": str(raw.get("glosa") or "")[:120],
                            "message": "Sin referencia externa",
                        }
                    )
                    continue

                glosa = str(raw.get("glosa") or "").strip() or f"Asiento {external_ref}"
                entry_date = self._parse_entry_date(raw.get("fecha"))
                number = self._libredte_number(raw, external_ref)

                exists = (
                    self.db.query(AccountingEntryModel.id)
                    .filter(AccountingEntryModel.external_ref == external_ref)
                    .first()
                )
                if exists:
                    skipped += 1
                    items.append(
                        {
                            "action": "skipped",
                            "external_ref": external_ref,
                            "number": number,
                            "fecha": entry_date.strftime("%Y-%m-%d"),
                            "glosa": glosa[:180],
                        }
                    )
                    continue

                operation = raw.get("operacion")
                if operation not in (None, "", "I", "E"):
                    operation = str(operation)[:8]
                period = entry_date.strftime("%Y-%m")

                entry = AccountingEntryModel(
                    number=number,
                    period=period,
                    entry_date=entry_date,
                    glosa=glosa[:512],
                    operation=operation or None,
                    annulled=0,
                    user_id=user_id,
                    source="libredte_import",
                    external_ref=external_ref[:128],
                    added_date=now,
                    updated_date=now,
                )
                self.db.add(entry)
                self.db.flush()

                for sort_order, line in enumerate(self._libredte_lines(raw)):
                    self.db.add(
                        AccountingEntryLineModel(
                            accounting_entry_id=entry.id,
                            account_code=line["account_code"][:32],
                            debit=line["debit"],
                            credit=line["credit"],
                            concept=line.get("concept"),
                            sort_order=sort_order,
                        )
                    )

                for doc in self._libredte_documents(raw, period):
                    self.db.add(
                        AccountingEntryDocumentModel(
                            accounting_entry_id=entry.id,
                            doc_type=doc["doc_type"],
                            issuer_rut=doc.get("issuer_rut"),
                            dte_type_id=doc.get("dte_type_id"),
                            folio=doc.get("folio"),
                            period=doc.get("period") or period,
                        )
                    )

                self.db.commit()
                imported += 1
                items.append(
                    {
                        "action": "imported",
                        "external_ref": external_ref,
                        "number": number,
                        "fecha": entry_date.strftime("%Y-%m-%d"),
                        "glosa": glosa[:180],
                    }
                )
            except Exception as exc:
                self.db.rollback()
                print(f"[accounting_entry.import] error: {exc}", flush=True)
                errors += 1
                items.append(
                    {
                        "action": "error",
                        "glosa": str(raw.get("glosa") or "")[:120],
                        "message": str(exc)[:180],
                    }
                )
                continue

        return {
            "status": "success",
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
            "total_libredte": len(entries),
            "since": since,
            "until": until,
            "items": items,
        }

    def _libredte_external_ref(self, raw: dict) -> Optional[str]:
        entry_id = raw.get("id")
        if entry_id:
            return str(entry_id).strip()
        asiento = raw.get("asiento") or raw.get("codigo")
        fecha = str(raw.get("fecha") or "")[:10]
        year = fecha.split("-")[0] if fecha else ""
        if asiento not in (None, "") and year:
            return f"{year}-{asiento}"
        if asiento not in (None, ""):
            return str(asiento)
        return None

    def _libredte_number(self, raw: dict, external_ref: str) -> int:
        for key in ("asiento", "codigo"):
            if raw.get(key) not in (None, ""):
                try:
                    return int(raw.get(key))
                except (TypeError, ValueError):
                    pass
        if "-" in external_ref:
            try:
                return int(external_ref.split("-")[-1])
            except (TypeError, ValueError):
                pass
        return self._next_number(datetime.now().year)

    def _libredte_lines(self, raw: dict) -> list:
        lines = []
        detalle = raw.get("detalle")
        if isinstance(detalle, list):
            for item in detalle:
                if not isinstance(item, dict):
                    continue
                code = str(
                    item.get("cuenta_codigo")
                    or item.get("cuenta")
                    or item.get("codigo")
                    or ""
                ).strip()
                if not code:
                    continue
                try:
                    debit = int(round(float(item.get("debe") or 0)))
                except (TypeError, ValueError):
                    debit = 0
                try:
                    credit = int(round(float(item.get("haber") or 0)))
                except (TypeError, ValueError):
                    credit = 0
                if debit == 0 and credit == 0:
                    continue
                lines.append(
                    {
                        "account_code": code,
                        "debit": abs(debit),
                        "credit": abs(credit),
                        "concept": item.get("cuenta_glosa") or item.get("glosa") or None,
                    }
                )
            return lines

        if isinstance(detalle, dict):
            debe = detalle.get("debe") or {}
            haber = detalle.get("haber") or {}
            if isinstance(debe, dict):
                for code, amount in debe.items():
                    try:
                        amt = int(round(float(amount or 0)))
                    except (TypeError, ValueError):
                        amt = 0
                    if amt:
                        lines.append(
                            {
                                "account_code": str(code).strip(),
                                "debit": abs(amt),
                                "credit": 0,
                                "concept": None,
                            }
                        )
            if isinstance(haber, dict):
                for code, amount in haber.items():
                    try:
                        amt = int(round(float(amount or 0)))
                    except (TypeError, ValueError):
                        amt = 0
                    if amt:
                        lines.append(
                            {
                                "account_code": str(code).strip(),
                                "debit": 0,
                                "credit": abs(amt),
                                "concept": None,
                            }
                        )
        return lines

    def _libredte_documents(self, raw: dict, period: str) -> list:
        docs = []
        documentos = raw.get("documentos") or {}
        if isinstance(documentos, list):
            for doc in documentos:
                if not isinstance(doc, dict):
                    continue
                docs.append(
                    {
                        "doc_type": "emitido",
                        "issuer_rut": str(doc.get("rut") or "") or None,
                        "dte_type_id": int(doc.get("dte") or 0) or None,
                        "folio": int(doc.get("folio") or 0) or None,
                        "period": period,
                    }
                )
            return docs

        if isinstance(documentos, dict):
            for key, doc_type in (("emitidos", "emitido"), ("recibidos", "recibido")):
                for doc in documentos.get(key) or []:
                    if not isinstance(doc, dict):
                        continue
                    try:
                        folio = int(doc.get("folio") or 0) or None
                    except (TypeError, ValueError):
                        folio = None
                    try:
                        dte_type_id = int(doc.get("dte") or 0) or None
                    except (TypeError, ValueError):
                        dte_type_id = None
                    docs.append(
                        {
                            "doc_type": doc_type,
                            "issuer_rut": str(doc.get("rut") or "") or None,
                            "dte_type_id": dte_type_id,
                            "folio": folio,
                            "period": period,
                        }
                    )
        return docs

    def list_accounts(self, active_only=True):
        query = self.db.query(AccountingAccountModel)
        if active_only:
            query = query.filter(AccountingAccountModel.status_id == 1)
        rows = query.order_by(AccountingAccountModel.code.asc()).all()
        return [
            {"id": r.id, "code": r.code, "name": r.name, "status_id": r.status_id}
            for r in rows
        ]

    def search_accounts(
        self,
        code=None,
        name=None,
        status_id=None,
        page=1,
        items_per_page=10,
    ):
        query = self.db.query(AccountingAccountModel)
        if code:
            query = query.filter(AccountingAccountModel.code.ilike(f"%{str(code).strip()}%"))
        if name:
            query = query.filter(AccountingAccountModel.name.ilike(f"%{str(name).strip()}%"))
        if status_id not in (None, ""):
            query = query.filter(AccountingAccountModel.status_id == int(status_id))

        total_items = query.count()
        page = max(1, int(page or 1))
        items_per_page = max(1, int(items_per_page or 10))
        total_pages = (total_items + items_per_page - 1) // items_per_page if total_items else 0
        rows = (
            query.order_by(AccountingAccountModel.code.asc())
            .offset((page - 1) * items_per_page)
            .limit(items_per_page)
            .all()
        )
        return {
            "data": [
                {"id": r.id, "code": r.code, "name": r.name, "status_id": r.status_id}
                for r in rows
            ],
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page,
            "items_per_page": items_per_page,
        }

    def get_account(self, account_id: int):
        row = (
            self.db.query(AccountingAccountModel)
            .filter(AccountingAccountModel.id == account_id)
            .first()
        )
        if not row:
            return {"status": "error", "message": "Cuenta no encontrada"}
        return {
            "status": "success",
            "data": {
                "id": row.id,
                "code": row.code,
                "name": row.name,
                "status_id": row.status_id,
            },
        }

    def store_account(self, code: str, name: str, status_id: int = 1):
        code = str(code or "").strip()
        name = str(name or "").strip()
        if not code or not name:
            return {"status": "error", "message": "Código y nombre son obligatorios"}
        exists = (
            self.db.query(AccountingAccountModel.id)
            .filter(AccountingAccountModel.code == code)
            .first()
        )
        if exists:
            return {"status": "error", "message": "El código de cuenta ya existe"}
        now = datetime.now()
        try:
            status_value = int(status_id or 1)
        except (TypeError, ValueError):
            status_value = 1
        if status_value not in (0, 1):
            status_value = 1
        row = AccountingAccountModel(
            code=code,
            name=name,
            status_id=status_value,
            added_date=now,
            updated_date=now,
        )
        self.db.add(row)
        self.db.commit()
        return {"status": "success", "id": row.id, "code": row.code}

    def update_account(self, account_id: int, code: str, name: str, status_id: int = 1):
        row = (
            self.db.query(AccountingAccountModel)
            .filter(AccountingAccountModel.id == account_id)
            .first()
        )
        if not row:
            return {"status": "error", "message": "Cuenta no encontrada"}
        code = str(code or "").strip()
        name = str(name or "").strip()
        if not code or not name:
            return {"status": "error", "message": "Código y nombre son obligatorios"}
        exists = (
            self.db.query(AccountingAccountModel.id)
            .filter(
                AccountingAccountModel.code == code,
                AccountingAccountModel.id != account_id,
            )
            .first()
        )
        if exists:
            return {"status": "error", "message": "El código de cuenta ya existe"}
        try:
            status_value = int(status_id)
        except (TypeError, ValueError):
            status_value = 1
        if status_value not in (0, 1):
            status_value = 1
        row.code = code
        row.name = name
        row.status_id = status_value
        row.updated_date = datetime.now()
        self.db.commit()
        return {"status": "success", "id": row.id}

    def delete_account(self, account_id: int):
        row = (
            self.db.query(AccountingAccountModel)
            .filter(AccountingAccountModel.id == account_id)
            .first()
        )
        if not row:
            return {"status": "error", "message": "Cuenta no encontrada"}
        row.status_id = 0
        row.updated_date = datetime.now()
        self.db.commit()
        return {"status": "success", "id": row.id}


def _safe_json(response):
    try:
        return response.json()
    except Exception:
        return (response.text or "")[:500]
