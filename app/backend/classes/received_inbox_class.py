from sqlalchemy.orm import Session
from sqlalchemy.dialects import mysql
from app.backend.db.models import (
    ReceivedInboxModel,
    BranchOfficeModel,
    DteModel,
    SupplierModel,
)
from app.backend.classes.helper_class import HelperClass
from app.backend.classes.customer_ticket_class import (
    CustomerTicketClass,
    SIMPLEFACTURA_AMBIENTE,
    SIMPLEFACTURA_RUT_EMISOR,
    SIMPLEFACTURA_SUCURSAL,
)
from datetime import datetime, timedelta
import json
import os
import base64
import uuid
import requests

SIMPLEFACTURA_DOCUMENTS_RECEIVED_URL = "https://api.simplefactura.cl/documentsReceived"
SIMPLEFACTURA_CONSOLIDATE_RECEIVED_URL = "https://api.simplefactura.cl/documentsReceived/consolidate"
SIMPLEFACTURA_ACKNOWLEDGMENT_URL = "https://api.simplefactura.cl/acknowledgmentReceipt"
SIMPLEFACTURA_RECEIVED_PDF_URL = "https://api.simplefactura.cl/documentReceived/getPdf"
SIMPLEFACTURA_RECEIVED_XML_URL = "https://api.simplefactura.cl/documentReceived/xml"
SIMPLEFACTURA_RECEIVED_TIMEOUT = int(os.getenv("SIMPLEFACTURA_RECEIVED_TIMEOUT", "45"))
SIMPLEFACTURA_CONSOLIDATE_MONTHS = int(os.getenv("SIMPLEFACTURA_CONSOLIDATE_MONTHS", "1"))
RECEIVED_INBOX_LOOKBACK_DAYS = int(os.getenv("RECEIVED_INBOX_LOOKBACK_DAYS", "30"))
RECEIVED_DTE_TYPES = (33, 34, 39, 61)
DTE_TYPE_LABELS = {
    33: "FACTURA ELECTRÓNICA",
    34: "FACTURA EXENTA ELECTRÓNICA",
    39: "BOLETA ELECTRÓNICA",
    41: "BOLETA EXENTA ELECTRÓNICA",
    52: "GUÍA DE DESPACHO ELECTRÓNICA",
    56: "NOTA DE DÉBITO ELECTRÓNICA",
    61: "NOTA DE CRÉDITO ELECTRÓNICA",
}
RECEIVED_INBOX_STATUS_PENDING = 1
RECEIVED_INBOX_STATUS_ACCEPTED = 2
RECEIVED_INBOX_STATUS_REJECTED = 3
SIMPLEFACTURA_RESPONSE_ACCEPTED = 3
SIMPLEFACTURA_RESPONSE_REJECTED = 5


class ReceivedInboxClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, page=0, items_per_page=10):
        try:
            query = self._base_query()
            if page > 0:
                return self._paginate(query, page, items_per_page)
            data = query.all()
            return self._serialize_rows(data)
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def search(
        self,
        folio=None,
        branch_office_id=None,
        rut=None,
        supplier=None,
        since=None,
        until=None,
        amount=None,
        status_id=None,
        dte_type_id=None,
        page=1,
        items_per_page=10,
    ):
        try:
            if page is None or page < 1:
                page = 1

            def _filled(val):
                if val is None:
                    return False
                if isinstance(val, str) and val.strip() == "":
                    return False
                return True

            filters = []
            if _filled(folio):
                try:
                    filters.append(ReceivedInboxModel.folio == int(str(folio).strip()))
                except (ValueError, TypeError):
                    filters.append(ReceivedInboxModel.folio == folio)
            if branch_office_id is not None:
                filters.append(ReceivedInboxModel.branch_office_id == branch_office_id)
            if _filled(rut):
                filters.append(ReceivedInboxModel.rut == str(rut).strip())
            if _filled(supplier):
                filters.append(ReceivedInboxModel.supplier.like(f"%{str(supplier).strip()}%"))
            if _filled(until):
                filters.append(ReceivedInboxModel.added_date <= str(until).strip())
            if _filled(since):
                filters.append(ReceivedInboxModel.added_date >= str(since).strip())
            if _filled(amount):
                try:
                    filters.append(ReceivedInboxModel.total == int(str(amount).strip()))
                except (ValueError, TypeError):
                    filters.append(ReceivedInboxModel.total == amount)
            if status_id is not None:
                filters.append(ReceivedInboxModel.status_id == status_id)
            if dte_type_id is not None:
                filters.append(ReceivedInboxModel.dte_type_id == dte_type_id)
            else:
                filters.append(ReceivedInboxModel.dte_type_id.in_(list(RECEIVED_DTE_TYPES)))

            query = self._base_query().filter(*filters) if filters else self._base_query()
            return self._paginate(query, page, items_per_page)
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _base_query(self):
        return (
            self.db.query(
                ReceivedInboxModel.id,
                ReceivedInboxModel.branch_office_id,
                ReceivedInboxModel.folio,
                ReceivedInboxModel.total,
                ReceivedInboxModel.added_date,
                ReceivedInboxModel.rut,
                ReceivedInboxModel.status_id,
                ReceivedInboxModel.dte_type_id,
                ReceivedInboxModel.supplier,
                ReceivedInboxModel.acknowledgment_status,
                ReceivedInboxModel.environment,
                BranchOfficeModel.branch_office,
            )
            .outerjoin(
                BranchOfficeModel,
                BranchOfficeModel.id == ReceivedInboxModel.branch_office_id,
            )
            .order_by(ReceivedInboxModel.id.desc())
        )

    def _is_acknowledgment_pending(self, status_id, acknowledgment_status):
        if int(status_id or 0) in (
            RECEIVED_INBOX_STATUS_ACCEPTED,
            RECEIVED_INBOX_STATUS_REJECTED,
        ):
            return False
        acuse = str(acknowledgment_status or "").strip().lower()
        if acuse in ("3", "4", "5"):
            return False
        if any(
            token in acuse
            for token in (
                "acept",
                "conforme",
                "approved",
                "rechaz",
                "rejected",
            )
        ):
            return False
        return True

    def _ensure_supplier(self, rut, supplier_name):
        if not rut:
            return
        exists = (
            self.db.query(SupplierModel.id)
            .filter(SupplierModel.rut == rut)
            .first()
        )
        if exists:
            return
        supplier = SupplierModel()
        supplier.rut = rut
        supplier.supplier = (supplier_name or "").upper() or None
        self.db.add(supplier)

    def _ensure_received_dte(self, row):
        """
        After SII/SimpleFactura accept, mirror LibreDTE import into dtes
        (dte_version_id=2, status_id=1 = No revisada / Recibidas).
        """
        if not row or not row.rut or not row.folio:
            return {"created": False, "reason": "incomplete"}

        folio = int(row.folio)
        dte_type_id = int(row.dte_type_id or 0)
        rut = str(row.rut)

        existing = (
            self.db.query(DteModel.id)
            .filter(
                DteModel.dte_version_id == 2,
                DteModel.folio == folio,
                DteModel.rut == rut,
                DteModel.dte_type_id == dte_type_id,
            )
            .first()
        )
        if existing:
            return {"created": False, "reason": "exists", "dte_id": existing.id}

        self._ensure_supplier(rut, getattr(row, "supplier", None))

        total = int(row.total or 0)
        net = int(row.subtotal or 0)
        tax = int(row.tax if row.tax is not None else (total - net))
        if dte_type_id == 61:
            total = -abs(total)
            net = -abs(net)
            tax = int(total) - int(net)

        added_date = row.added_date or datetime.now()
        if row.document_date and not row.added_date:
            try:
                added_date = datetime.strptime(
                    str(row.document_date)[:10] + " 00:00:00",
                    "%Y-%m-%d %H:%M:%S",
                )
            except ValueError:
                added_date = datetime.now()

        dte = DteModel()
        dte.branch_office_id = int(row.branch_office_id or 0)
        dte.cashier_id = 0
        dte.dte_type_id = dte_type_id
        dte.dte_version_id = 2
        dte.status_id = 1
        dte.chip_id = 0
        dte.rut = rut
        dte.folio = folio
        dte.cash_amount = total
        dte.card_amount = 0
        dte.subtotal = net
        dte.tax = tax
        dte.discount = 0
        dte.total = total
        dte.added_date = added_date
        dte.updated_date = datetime.now()
        self.db.add(dte)
        self.db.flush()
        print(
            f"[received_inbox] created received dte id={dte.id} "
            f"folio={folio} rut={rut} type={dte_type_id}",
            flush=True,
        )
        return {"created": True, "dte_id": dte.id}

    def _map_acknowledgment_status(self, item):
        """
        SimpleFactura documentsReceived uses `estado` (e.g. RECIBIDO CONFORME),
        not always `estadoAcuse`.
        """
        raw = self._sf_item_value(
            item,
            "estadoAcuse",
            "EstadoAcuse",
            "estado",
            "Estado",
            "respuesta",
            "Respuesta",
        )
        text = str(raw or "").strip()
        if not text:
            return None, RECEIVED_INBOX_STATUS_PENDING

        lower = text.lower()
        if any(token in lower for token in ("rechaz", "rejected", "no conforme")):
            return text, RECEIVED_INBOX_STATUS_REJECTED
        if any(
            token in lower
            for token in ("conforme", "acept", "approved", "acuse acept")
        ):
            return text, RECEIVED_INBOX_STATUS_ACCEPTED
        return text, RECEIVED_INBOX_STATUS_PENDING

    def _serialize_rows(self, data):
        return [
            {
                "id": row.id,
                "rut": row.rut,
                "branch_office_id": row.branch_office_id,
                "supplier": row.supplier,
                "folio": row.folio,
                "total": row.total,
                "status_id": row.status_id,
                "dte_type_id": row.dte_type_id,
                "acknowledgment_status": row.acknowledgment_status,
                "can_acknowledge": self._is_acknowledgment_pending(row.status_id, row.acknowledgment_status),
                "added_date": row.added_date.strftime("%Y-%m-%d") if row.added_date else None,
                "branch_office": row.branch_office,
            }
            for row in data
        ]

    def _paginate(self, query, page, items_per_page):
        total_items = query.count()
        if total_items == 0:
            return {
                "status": "ok",
                "message": "No data found",
                "data": [],
                "total_items": 0,
                "total_pages": 0,
                "current_page": page,
                "items_per_page": items_per_page,
            }

        total_pages = (total_items + items_per_page - 1) // items_per_page
        if page < 1 or page > total_pages:
            return {"status": "error", "message": "Invalid page number"}

        data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()
        return {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page,
            "items_per_page": items_per_page,
            "data": self._serialize_rows(data),
            "mysql_base": str(
                query.statement.compile(
                    dialect=mysql.dialect(),
                    compile_kwargs={"literal_binds": True},
                )
            ),
        }

    def _sf_item_value(self, item, *keys, default=None):
        if not isinstance(item, dict):
            return default
        lower = {str(k).lower(): v for k, v in item.items()}
        for key in keys:
            if key in item and item[key] is not None:
                return item[key]
            value = lower.get(str(key).lower())
            if value is not None:
                return value
        return default

    def _sf_normalize_rut(self, value):
        if value is None:
            return None
        raw = str(value).strip().upper().replace(".", "").replace(" ", "")
        if not raw:
            return None
        if "-" in raw:
            body, dv = raw.split("-", 1)
            if body.isdigit() and dv:
                return f"{int(body)}-{dv}"
            return raw
        digits = "".join(ch for ch in raw if ch.isdigit())
        if not digits:
            return None
        digits = str(int(digits))
        return f"{digits}-{HelperClass.verificator_digit(digits)}"

    def _sf_parse_date(self, value):
        if not value:
            return ""
        text = str(value).strip()
        if not text:
            return ""
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(text[:26].replace("Z", ""), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        if "T" in text:
            return text.split("T", 1)[0]
        return text[:10]

    def _sf_dte_type_id(self, item):
        codigo = self._sf_item_value(item, "codigoSii", "CodigoSii", "codigoTipoDte", "CodigoTipoDte")
        try:
            if codigo is not None and str(codigo).strip() != "":
                return int(codigo)
        except (TypeError, ValueError):
            pass
        tipo = self._sf_item_value(item, "tipoDte", "TipoDte", "tipoDTE")
        try:
            return int(tipo)
        except (TypeError, ValueError):
            return 0

    def _simplefactura_token(self):
        ticket_class = CustomerTicketClass(self.db)
        forced = (os.getenv("DTE_V2_FORCE_TOKEN") or os.getenv("SIMPLEFACTURA_FORCE_TOKEN") or "").strip()
        if forced:
            return forced, ticket_class
        result = ticket_class.get_token()
        if result.get("status") != "success":
            raise ValueError(result.get("message") or "No se pudo obtener token SimpleFactura")
        token = result.get("accessToken")
        if not token:
            raise ValueError("Token SimpleFactura vacío")
        return token, ticket_class

    def _simplefactura_post(self, url, payload):
        token, ticket_class = self._simplefactura_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=SIMPLEFACTURA_RECEIVED_TIMEOUT,
            )
        except requests.Timeout as exc:
            raise ValueError(f"SimpleFactura timeout ({SIMPLEFACTURA_RECEIVED_TIMEOUT}s): {url}") from exc
        except requests.RequestException as exc:
            raise ValueError(f"SimpleFactura connection error: {exc}") from exc
        if response.status_code == 401:
            token = ticket_class.fetch_simplefactura_token_from_jisbackend()
            headers["Authorization"] = f"Bearer {token}"
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=SIMPLEFACTURA_RECEIVED_TIMEOUT,
                )
            except requests.Timeout as exc:
                raise ValueError(f"SimpleFactura timeout ({SIMPLEFACTURA_RECEIVED_TIMEOUT}s): {url}") from exc
            except requests.RequestException as exc:
                raise ValueError(f"SimpleFactura connection error: {exc}") from exc
        if response.status_code != 200:
            raise ValueError(
                f"SimpleFactura {url} HTTP {response.status_code}: {(response.text or '')[:400]}"
            )
        try:
            return response.json()
        except ValueError as exc:
            raise ValueError(f"SimpleFactura {url}: JSON inválido ({exc})") from exc

    def _simplefactura_post_bytes(self, url, payload):
        """POST that expects binary body (PDF)."""
        token, ticket_class = self._simplefactura_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=SIMPLEFACTURA_RECEIVED_TIMEOUT,
            )
        except requests.Timeout as exc:
            raise ValueError(f"SimpleFactura timeout ({SIMPLEFACTURA_RECEIVED_TIMEOUT}s): {url}") from exc
        except requests.RequestException as exc:
            raise ValueError(f"SimpleFactura connection error: {exc}") from exc
        if response.status_code == 401:
            token = ticket_class.fetch_simplefactura_token_from_jisbackend()
            headers["Authorization"] = f"Bearer {token}"
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=SIMPLEFACTURA_RECEIVED_TIMEOUT,
                )
            except requests.Timeout as exc:
                raise ValueError(f"SimpleFactura timeout ({SIMPLEFACTURA_RECEIVED_TIMEOUT}s): {url}") from exc
            except requests.RequestException as exc:
                raise ValueError(f"SimpleFactura connection error: {exc}") from exc
        if response.status_code != 200 or not response.content:
            raise ValueError(
                f"SimpleFactura {url} HTTP {response.status_code}: {(response.text or '')[:400]}"
            )
        if not response.content.startswith(b"%PDF"):
            # Some gateways wrap PDF in JSON/base64 — try unwrap
            try:
                body = response.json()
            except ValueError:
                body = None
            if isinstance(body, dict):
                data = body.get("data") or body.get("file") or body.get("pdf")
                if isinstance(data, str) and data.strip():
                    try:
                        raw = base64.b64decode(data)
                        if raw.startswith(b"%PDF"):
                            return raw
                    except Exception:
                        pass
            raise ValueError("SimpleFactura no devolvió un PDF válido")
        return response.content

    def _extract_dte_list(self, body):
        if isinstance(body, list):
            return body
        if not isinstance(body, dict):
            return None
        data = body.get("data")
        if isinstance(data, list):
            return data
        if isinstance(data, str):
            text = data.strip()
            if text.startswith("[") or text.startswith("{"):
                try:
                    parsed = json.loads(text)
                except ValueError:
                    parsed = None
                if isinstance(parsed, list):
                    return parsed
                if isinstance(parsed, dict):
                    return self._extract_dte_list(parsed)
            # consolidate often returns a plain text message, not a DTE list
            return []
        if isinstance(data, dict):
            for key in ("dtes", "documentos", "items", "list"):
                nested = data.get(key)
                if isinstance(nested, list):
                    return nested
        return None

    def _months_covering(self, since_dt, until_dt):
        months = []
        cursor = datetime(until_dt.year, until_dt.month, 1)
        start = datetime(since_dt.year, since_dt.month, 1)
        while cursor >= start:
            months.append((cursor.month, cursor.year))
            if cursor.month == 1:
                cursor = datetime(cursor.year - 1, 12, 1)
            else:
                cursor = datetime(cursor.year, cursor.month - 1, 1)
        return months

    def _consolidate_simplefactura_received(self, mes, anio):
        """POST /documentsReceived/consolidate/{mes}/{anio} — cruce con SII."""
        url = f"{SIMPLEFACTURA_CONSOLIDATE_RECEIVED_URL}/{int(mes)}/{int(anio)}"
        payloads = [
            {
                "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
                "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
            },
            {
                "credenciales": {
                    "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
                    "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
                },
                "ambiente": SIMPLEFACTURA_AMBIENTE,
            },
        ]
        last_error = None
        body = None
        for payload in payloads:
            try:
                body = self._simplefactura_post(url, payload)
                break
            except ValueError as exc:
                last_error = exc
                msg = str(exc)
                if "HTTP 400" not in msg and "timeout" not in msg.lower():
                    raise
        if body is None:
            raise last_error or ValueError("SimpleFactura consolidate: sin respuesta")
        items = self._extract_dte_list(body)
        message = None
        if isinstance(body, dict):
            message = body.get("message")
            if message is None and not isinstance(body.get("data"), list):
                message = body.get("data")
        return {
            "mes": int(mes),
            "anio": int(anio),
            "items": items or [],
            "message": str(message) if message not in (None, "") else None,
        }

    def _fetch_simplefactura_received_documents(self, since, until):
        payload = {
            "credenciales": {
                "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
                "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
            },
            "ambiente": SIMPLEFACTURA_AMBIENTE,
            "desde": since,
            "hasta": until,
        }
        body = self._simplefactura_post(SIMPLEFACTURA_DOCUMENTS_RECEIVED_URL, payload)
        items = self._extract_dte_list(body)
        if items is None:
            raise ValueError("SimpleFactura documentsReceived: respuesta sin listado")
        return items

    def refresh(self):
        """
        1) Conciliar solo el mes actual (SII → SimpleFactura).
        2) Listar documentsReceived y guardar en received_inbox.
        Evita colgarse reconciliando 3 meses seguidos.
        """
        until_dt = datetime.now()
        since_dt = until_dt - timedelta(days=max(1, RECEIVED_INBOX_LOOKBACK_DAYS))
        since = since_dt.strftime("%Y-%m-%d")
        until = until_dt.strftime("%Y-%m-%d")
        months_back = max(1, min(SIMPLEFACTURA_CONSOLIDATE_MONTHS, 3))
        consolidate_since = datetime(until_dt.year, until_dt.month, 1)
        for _ in range(months_back - 1):
            if consolidate_since.month == 1:
                consolidate_since = datetime(consolidate_since.year - 1, 12, 1)
            else:
                consolidate_since = datetime(consolidate_since.year, consolidate_since.month - 1, 1)

        summary = {
            "status": "success",
            "source": "simplefactura_sii_consolidate",
            "fetched": 0,
            "inserted": 0,
            "skipped": 0,
            "consolidated": [],
            "errors": [],
        }

        try:
            data = []
            seen_keys = set()

            for mes, anio in self._months_covering(consolidate_since, until_dt):
                try:
                    result = self._consolidate_simplefactura_received(mes, anio)
                    summary["consolidated"].append(
                        {
                            "mes": result["mes"],
                            "anio": result["anio"],
                            "count": len(result["items"]),
                            "message": result["message"],
                        }
                    )
                    for item in result["items"]:
                        if not isinstance(item, dict):
                            continue
                        key = (
                            self._sf_item_value(item, "folio", "Folio"),
                            self._sf_item_value(
                                item, "rutProveedor", "RutProveedor", "rutEmisor", "RutEmisor"
                            ),
                            self._sf_dte_type_id(item),
                        )
                        if key in seen_keys:
                            continue
                        seen_keys.add(key)
                        data.append(item)
                except Exception as exc:
                    err = f"consolidate {mes}/{anio}: {exc}"
                    summary["errors"].append(err)
                    summary["consolidated"].append(
                        {"mes": mes, "anio": anio, "count": 0, "message": str(exc)}
                    )
                    print(f"[received_inbox.refresh] {err}", flush=True)

            # El listado real suele venir de documentsReceived, no del consolidate.
            try:
                listed = self._fetch_simplefactura_received_documents(since, until)
                for item in listed:
                    if not isinstance(item, dict):
                        continue
                    key = (
                        self._sf_item_value(item, "folio", "Folio"),
                        self._sf_item_value(
                            item, "rutProveedor", "RutProveedor", "rutEmisor", "RutEmisor"
                        ),
                        self._sf_dte_type_id(item),
                    )
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    data.append(item)
            except Exception as exc:
                err = f"documentsReceived: {exc}"
                summary["errors"].append(err)
                print(f"[received_inbox.refresh] {err}", flush=True)
                if not data:
                    summary["status"] = "error"
                    return summary

            summary["fetched"] = len(data)
            persist = self._persist_received_items(data)
            summary["inserted"] = persist["inserted"]
            summary["skipped"] = persist["skipped"]
            summary["updated"] = persist.get("updated", 0)
            print(
                f"[received_inbox.refresh] source=sii_consolidate "
                f"fetched={summary['fetched']} inserted={summary['inserted']} "
                f"updated={summary['updated']} skipped={summary['skipped']} "
                f"consolidated={summary.get('consolidated')}",
                flush=True,
            )
            return summary
        except Exception as e:
            self.db.rollback()
            print("Error al conectar SimpleFactura / received_inbox:", e, flush=True)
            summary["status"] = "error"
            summary["errors"].append(str(e))
            return summary

    def import_plan(self):
        """Days to process (oldest → newest) for live SII import UI."""
        until_dt = datetime.now().date()
        lookback = max(1, RECEIVED_INBOX_LOOKBACK_DAYS)
        since_dt = until_dt - timedelta(days=lookback - 1)
        days = []
        cursor = since_dt
        while cursor <= until_dt:
            days.append(cursor.strftime("%Y-%m-%d"))
            cursor += timedelta(days=1)
        return {
            "status": "success",
            "lookback_days": lookback,
            "since": since_dt.strftime("%Y-%m-%d"),
            "until": until_dt.strftime("%Y-%m-%d"),
            "total_days": len(days),
            "days": days,
        }

    def import_day(self, date_str: str, consolidate: bool = False):
        """
        Import received DTEs for a single calendar day.
        Optionally consolidate that month with SII first.
        """
        try:
            day = datetime.strptime(str(date_str).strip()[:10], "%Y-%m-%d").date()
        except ValueError:
            return {"status": "error", "message": f"Invalid date: {date_str}"}

        day_iso = day.strftime("%Y-%m-%d")
        summary = {
            "status": "success",
            "date": day_iso,
            "fetched": 0,
            "inserted": 0,
            "skipped": 0,
            "consolidated": None,
            "errors": [],
        }

        try:
            if consolidate:
                try:
                    result = self._consolidate_simplefactura_received(day.month, day.year)
                    summary["consolidated"] = {
                        "mes": result["mes"],
                        "anio": result["anio"],
                        "message": result["message"],
                    }
                except Exception as exc:
                    err = f"consolidate {day.month}/{day.year}: {exc}"
                    summary["errors"].append(err)
                    print(f"[received_inbox.import_day] {err}", flush=True)

            data = self._fetch_simplefactura_received_documents(day_iso, day_iso)
            summary["fetched"] = len(data)
            persist = self._persist_received_items(data)
            summary["inserted"] = persist["inserted"]
            summary["skipped"] = persist["skipped"]
            summary["updated"] = persist.get("updated", 0)
            print(
                f"[received_inbox.import_day] date={day_iso} "
                f"fetched={summary['fetched']} inserted={summary['inserted']} "
                f"updated={summary['updated']} skipped={summary['skipped']}",
                flush=True,
            )
            return summary
        except Exception as e:
            self.db.rollback()
            print(f"[received_inbox.import_day] error date={day_iso}: {e}", flush=True)
            summary["status"] = "error"
            summary["errors"].append(str(e))
            return summary

    def _persist_received_items(self, data):
        """Insert new received inbox rows; update status on existing ones."""
        existing_rows = self.db.query(ReceivedInboxModel).all()
        existing_by_key = {
            (int(row.folio or 0), str(row.rut), int(row.dte_type_id or 0)): row
            for row in existing_rows
        }

        inserted = 0
        skipped = 0
        updated = 0
        now = datetime.now()
        for item in data:
            if not isinstance(item, dict):
                continue
            dte_type_id = self._sf_dte_type_id(item)
            if dte_type_id not in RECEIVED_DTE_TYPES:
                continue

            try:
                folio = int(self._sf_item_value(item, "folio", "Folio") or 0)
            except (TypeError, ValueError):
                folio = 0
            if folio <= 0:
                skipped += 1
                continue

            rut = self._sf_normalize_rut(
                self._sf_item_value(
                    item,
                    "rutProveedor",
                    "RutProveedor",
                    "rutEmisor",
                    "RutEmisor",
                )
            )
            if not rut:
                skipped += 1
                continue

            key = (folio, rut, dte_type_id)
            acknowledgment_status, status_id = self._map_acknowledgment_status(item)
            document_status = (
                str(self._sf_item_value(item, "estado", "Estado") or "") or None
            )
            sii_status = (
                str(self._sf_item_value(item, "estadoSII", "EstadoSII") or "") or None
            )
            environment = (
                str(self._sf_item_value(item, "ambiente", "Ambiente") or "") or None
            )

            existing = existing_by_key.get(key)
            if existing:
                changed = False
                if acknowledgment_status and existing.acknowledgment_status != acknowledgment_status:
                    existing.acknowledgment_status = acknowledgment_status
                    changed = True
                if existing.status_id != status_id:
                    existing.status_id = status_id
                    changed = True
                if document_status and existing.document_status != document_status:
                    existing.document_status = document_status
                    changed = True
                if sii_status and existing.sii_status != sii_status:
                    existing.sii_status = sii_status
                    changed = True
                if changed:
                    existing.updated_date = now
                    updated += 1
                else:
                    skipped += 1
                if status_id == RECEIVED_INBOX_STATUS_ACCEPTED:
                    self._ensure_received_dte(existing)
                continue

            supplier_name = (
                self._sf_item_value(
                    item,
                    "razonSocialProveedor",
                    "RazonSocialProveedor",
                    "razonSocialEmisor",
                    "RazonSocialEmisor",
                )
                or ""
            )
            try:
                total = int(float(self._sf_item_value(item, "total", "Total") or 0))
            except (TypeError, ValueError):
                total = 0
            try:
                net = int(float(self._sf_item_value(item, "neto", "Neto") or 0))
            except (TypeError, ValueError):
                net = 0
            if dte_type_id == 61:
                total = -abs(total)
                net = -abs(net)

            fecha = self._sf_parse_date(
                self._sf_item_value(
                    item,
                    "fechaDte",
                    "FechaDte",
                    "fechaEmision",
                    "FechaEmision",
                    "fechaCreacion",
                    "FechaCreacion",
                )
            )
            document_date = None
            added_date = now
            if fecha:
                try:
                    document_date = datetime.strptime(fecha, "%Y-%m-%d").date()
                    added_date = datetime.strptime(fecha + " 00:00:00", "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass

            track_raw = self._sf_item_value(item, "trackId", "TrackId")
            try:
                track_id = int(track_raw) if track_raw is not None else None
            except (TypeError, ValueError):
                track_id = None

            row = ReceivedInboxModel(
                rut=rut,
                supplier=str(supplier_name).upper() if supplier_name else None,
                branch_office_id=0,
                folio=folio,
                dte_type_id=dte_type_id,
                status_id=status_id,
                subtotal=net,
                tax=int(total) - int(net),
                total=total,
                environment=environment,
                document_status=document_status,
                sii_status=sii_status,
                acknowledgment_status=acknowledgment_status,
                track_id=track_id,
                document_date=document_date,
                added_date=added_date,
                updated_date=now,
            )
            self.db.add(row)
            self.db.flush()
            existing_by_key[key] = row
            inserted += 1
            if status_id == RECEIVED_INBOX_STATUS_ACCEPTED:
                self._ensure_received_dte(row)

        self.db.commit()
        return {"inserted": inserted, "skipped": skipped, "updated": updated}

    def acknowledge(self, form_data):
        """Accept or reject via SimpleFactura POST /acknowledgmentReceipt."""
        action = str(getattr(form_data, "action", "") or "").strip().lower()
        if action not in ("accept", "reject"):
            return {"status": "error", "message": "action must be accept or reject"}

        row = (
            self.db.query(ReceivedInboxModel)
            .filter(ReceivedInboxModel.id == int(form_data.id))
            .first()
        )
        if not row:
            return {"status": "error", "message": "Received inbox DTE not found"}
        if not self._is_acknowledgment_pending(row.status_id, row.acknowledgment_status):
            return {"status": "error", "message": "DTE already accepted or rejected"}

        comment = (getattr(form_data, "comment", None) or "").strip()
        if action == "reject" and not comment:
            comment = "Rejected"

        try:
            environment = SIMPLEFACTURA_AMBIENTE
            try:
                if row.environment not in (None, ""):
                    environment = int(row.environment)
            except (TypeError, ValueError):
                environment = SIMPLEFACTURA_AMBIENTE

            payload = {
                "credenciales": {
                    "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
                    "rutContribuyente": row.rut,
                    "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
                },
                "dteReferenciadoExterno": {
                    "folio": int(row.folio),
                    "codigoTipoDte": int(row.dte_type_id),
                    "ambiente": environment,
                },
                "respuesta": (
                    SIMPLEFACTURA_RESPONSE_ACCEPTED
                    if action == "accept"
                    else SIMPLEFACTURA_RESPONSE_REJECTED
                ),
                "tipo_rechazo": (
                    None
                    if action == "accept"
                    else int(getattr(form_data, "rejection_type_id", None) or 1)
                ),
                "comentario": comment or None,
            }
            body = self._simplefactura_post(SIMPLEFACTURA_ACKNOWLEDGMENT_URL, payload)

            now = datetime.now()
            if action == "accept":
                row.status_id = RECEIVED_INBOX_STATUS_ACCEPTED
                row.acknowledgment_status = "RECIBIDO CONFORME"
                row.document_status = row.document_status or "RECIBIDO CONFORME"
            else:
                row.status_id = RECEIVED_INBOX_STATUS_REJECTED
                row.acknowledgment_status = "Rejected"
            row.updated_date = now

            dte_result = None
            if action == "accept":
                dte_result = self._ensure_received_dte(row)

            self.db.commit()
            return {
                "status": "success",
                "action": action,
                "id": row.id,
                "received_dte": dte_result,
                "simplefactura": body,
            }
        except Exception as exc:
            self.db.rollback()
            return {"status": "error", "message": str(exc)}

    def download_pdf(self, id: int):
        """PDF of a received DTE via SimpleFactura (getPdf → XML render → LibreDTE)."""
        row = (
            self.db.query(ReceivedInboxModel)
            .filter(ReceivedInboxModel.id == int(id))
            .first()
        )
        if not row:
            return {"status": "error", "message": "Documento no encontrado"}

        environment = SIMPLEFACTURA_AMBIENTE
        try:
            if row.environment not in (None, ""):
                environment = int(row.environment)
        except (TypeError, ValueError):
            environment = SIMPLEFACTURA_AMBIENTE

        pdf_content = None
        errors = []
        sf_payload = {
            "credenciales": {
                "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
                "rutContribuyente": str(row.rut or "").strip(),
                "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
            },
            "ambiente": environment,
            "folio": int(row.folio),
            "codigoTipoDte": int(row.dte_type_id),
        }

        # 1) SimpleFactura documentReceived/getPdf
        try:
            pdf_content = self._simplefactura_post_bytes(SIMPLEFACTURA_RECEIVED_PDF_URL, sf_payload)
        except Exception as exc:
            errors.append(f"SimpleFactura getPdf: {exc}")

        # 2) SimpleFactura XML → PDF local (cuando no hay plantilla activa en SF)
        if not pdf_content:
            try:
                xml_bytes = self._fetch_received_xml_bytes(sf_payload)
                pdf_content = self._pdf_from_received_dte_xml(xml_bytes, row)
            except Exception as exc:
                errors.append(f"SimpleFactura XML→PDF: {exc}")

        # 3) LibreDTE dte_recibidos/pdf (fallback)
        if not pdf_content:
            try:
                issuer_rut = HelperClass().numeric_rut(row.rut)
                url = (
                    f"https://libredte.cl/api/dte/dte_recibidos/pdf/"
                    f"{issuer_rut}/{int(row.dte_type_id)}/{int(row.folio)}/76063822"
                    f"?papelContinuo=0&copias_tributarias=1&copias_cedibles=0"
                    f"&cedible=0&compress=0&base64=0"
                )
                token = (
                    os.getenv("LIBREDTE_API_TOKEN")
                    or os.getenv("LIBREDTE_DTE_TOKEN")
                    or "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
                )
                response = requests.get(
                    url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/pdf, application/octet-stream, */*",
                    },
                    timeout=SIMPLEFACTURA_RECEIVED_TIMEOUT,
                )
                if response.status_code == 200 and response.content.startswith(b"%PDF"):
                    pdf_content = response.content
                else:
                    errors.append(
                        f"LibreDTE HTTP {response.status_code}: {(response.text or '')[:200]}"
                    )
            except Exception as exc:
                errors.append(f"LibreDTE: {exc}")

        if not pdf_content:
            return {
                "status": "error",
                "message": "No se pudo obtener el PDF del documento recibido. "
                + (" | ".join(errors) if errors else ""),
            }

        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        file_name = f"recibido_{row.dte_type_id}_{row.folio}_{timestamp}_{unique_id}.pdf"
        return {
            "status": "success",
            "file_name": file_name,
            "file_data": base64.b64encode(pdf_content).decode("utf-8"),
        }

    def _fetch_received_xml_bytes(self, payload: dict) -> bytes:
        body = self._simplefactura_post(SIMPLEFACTURA_RECEIVED_XML_URL, payload)
        if not isinstance(body, dict):
            raise ValueError("Respuesta XML inválida")
        data = body.get("data")
        if isinstance(data, str) and data.strip():
            raw = base64.b64decode(data)
            if raw.lstrip().startswith(b"<?xml") or raw.lstrip().startswith(b"<"):
                return raw
            raise ValueError("data XML no es XML válido")
        if isinstance(data, (bytes, bytearray)) and data:
            return bytes(data)
        raise ValueError(body.get("message") or "Sin XML del documento recibido")

    @staticmethod
    def _xml_local(tag: str) -> str:
        if not tag:
            return ""
        if "}" in tag:
            return tag.rsplit("}", 1)[-1]
        return tag

    def _xml_find_text(self, root, *names) -> str:
        wanted = {n.lower() for n in names}
        for el in root.iter():
            if self._xml_local(el.tag).lower() in wanted:
                text = (el.text or "").strip()
                if text:
                    return text
        return ""

    def _xml_find_all(self, root, name: str):
        name_l = name.lower()
        return [el for el in root.iter() if self._xml_local(el.tag).lower() == name_l]

    @staticmethod
    def _format_cl_rut(rut: str) -> str:
        text = (rut or "").strip().upper().replace(".", "")
        if "-" in text:
            body, dv = text.rsplit("-", 1)
        elif len(text) > 1:
            body, dv = text[:-1], text[-1]
        else:
            return text
        body = "".join(ch for ch in body if ch.isdigit())
        if not body:
            return text
        parts = []
        while body:
            parts.insert(0, body[-3:])
            body = body[:-3]
        return f"{'.'.join(parts)}-{dv}"

    @staticmethod
    def _format_cl_money(value, decimals: int = 0) -> str:
        if value in (None, ""):
            return "—"
        try:
            num = float(str(value).replace(".", "").replace(",", ".")) if isinstance(value, str) and "," in str(value) else float(value)
        except (TypeError, ValueError):
            return str(value)
        if decimals <= 0:
            return f"{int(round(num)):,}".replace(",", ".")
        formatted = f"{num:,.{decimals}f}"
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")

    @staticmethod
    def _format_cl_long_date(iso_date: str) -> str:
        from datetime import datetime as dt

        text = (iso_date or "").strip()[:10]
        try:
            d = dt.strptime(text, "%Y-%m-%d")
        except ValueError:
            return text or ""
        weekdays = (
            "Lunes",
            "Martes",
            "Miércoles",
            "Jueves",
            "Viernes",
            "Sábado",
            "Domingo",
        )
        months = (
            "enero",
            "febrero",
            "marzo",
            "abril",
            "mayo",
            "junio",
            "julio",
            "agosto",
            "septiembre",
            "octubre",
            "noviembre",
            "diciembre",
        )
        return f"{weekdays[d.weekday()]} {d.day} de {months[d.month - 1]} del {d.year}"

    def _xml_block_fields(self, root, block_name: str) -> dict:
        fields = {}
        for el in root.iter():
            if self._xml_local(el.tag).lower() != block_name.lower():
                continue
            for child in el:
                ln = self._xml_local(child.tag)
                val = (child.text or "").strip()
                if ln and val:
                    fields[ln] = val
            break
        return fields

    def _pdf_from_received_dte_xml(self, xml_bytes: bytes, row) -> bytes:
        """Professional Chilean DTE PDF (LibreDTE-like layout, without LibreDTE branding)."""
        import io
        import re
        import xml.etree.ElementTree as ET
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader

        root = ET.fromstring(xml_bytes)
        tipo_raw = self._xml_find_text(root, "TipoDTE") or str(row.dte_type_id or "")
        try:
            tipo = int(tipo_raw)
        except (TypeError, ValueError):
            tipo = 0
        folio = self._xml_find_text(root, "Folio") or str(row.folio or "")
        fch = self._xml_find_text(root, "FchEmis") or str(getattr(row, "added_date", "") or "")
        fma_pago = self._xml_find_text(root, "FmaPago")
        venta = "crédito" if str(fma_pago) == "2" else "contado"

        emisor = self._xml_block_fields(root, "Emisor")
        receptor = self._xml_block_fields(root, "Receptor")
        emisor_name = emisor.get("RznSoc") or (row.supplier or "")
        emisor_rut = emisor.get("RUTEmisor") or str(row.rut or "")
        emisor_giro = emisor.get("GiroEmis") or ""
        emisor_dir = ", ".join(
            p for p in (
                emisor.get("DirOrigen"),
                emisor.get("CmnaOrigen"),
                emisor.get("CiudadOrigen"),
            ) if p
        )
        emisor_contact = " / ".join(
            p for p in (emisor.get("Telefono"), emisor.get("CorreoEmisor")) if p
        )
        receptor_name = receptor.get("RznSocRecep") or "JIS PARKING SPA"
        receptor_rut = receptor.get("RUTRecep") or SIMPLEFACTURA_RUT_EMISOR
        receptor_giro = receptor.get("GiroRecep") or ""
        receptor_dir = ", ".join(
            p for p in (
                receptor.get("DirRecep"),
                receptor.get("CmnaRecep"),
                receptor.get("CiudadRecep"),
            ) if p
        )
        receptor_contact = " / ".join(
            p for p in (receptor.get("Contacto"), receptor.get("CorreoRecep")) if p
        )

        mnt_neto = self._xml_find_text(root, "MntNeto")
        mnt_exento = self._xml_find_text(root, "MntExe")
        tasa_iva = self._xml_find_text(root, "TasaIVA") or "19"
        mnt_iva = self._xml_find_text(root, "IVA")
        mnt_total = self._xml_find_text(root, "MntTotal") or str(row.total or "")
        vlr_pagar = self._xml_find_text(root, "VlrPagar") or mnt_total
        tipo_label = DTE_TYPE_LABELS.get(tipo, f"DTE {tipo_raw}")
        sii_office = (emisor.get("CmnaOrigen") or emisor.get("CiudadOrigen") or "SANTIAGO").upper()

        details = []
        for det in self._xml_find_all(root, "Detalle"):
            item = {}
            for child in list(det):
                ln = self._xml_local(child.tag)
                val = (child.text or "").strip()
                if ln and val:
                    item[ln] = val
            name = item.get("NmbItem") or item.get("DscItem") or "—"
            dsc = item.get("DscItem") or name
            qty = item.get("QtyItem") or "1"
            unit = item.get("UnmdItem") or "Unid"
            price = item.get("PrcItem")
            total = item.get("MontoItem") or "0"
            if price in (None, "") and qty:
                try:
                    price = str(round(float(total) / float(qty), 1))
                except (TypeError, ValueError, ZeroDivisionError):
                    price = total
            details.append(
                {
                    "name": name,
                    "dsc": dsc,
                    "qty": qty,
                    "unit": unit,
                    "price": price,
                    "total": total,
                }
            )
        if not details:
            details.append(
                {
                    "name": emisor_name or "Documento recibido",
                    "dsc": emisor_name or "Documento recibido",
                    "qty": "1",
                    "unit": "Unid",
                    "price": mnt_total,
                    "total": mnt_total,
                }
            )

        # TED → PDF417
        ted_img = None
        ted_match = re.search(rb"<TED[^>]*>.*?</TED>", xml_bytes, re.DOTALL | re.IGNORECASE)
        if ted_match:
            try:
                from pdf417gen import encode, render_image

                ted_xml = ted_match.group(0).decode("iso-8859-1", errors="replace")
                ted_xml = re.sub(r">\s+<", "><", ted_xml)
                codes = encode(ted_xml, columns=12, security_level=5)
                pil_img = render_image(codes, scale=2, ratio=3)
                ted_buf = io.BytesIO()
                pil_img.save(ted_buf, format="PNG")
                ted_buf.seek(0)
                ted_img = ImageReader(ted_buf)
            except Exception:
                ted_img = None

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        width, height = letter
        left = 15 * mm
        right = width - 15 * mm
        usable = right - left
        y = height - 16 * mm

        blue = (0.08, 0.25, 0.55)
        red = (0.75, 0.05, 0.05)

        # ---- Header: emisor (left) + caja RUT (right) ----
        box_w, box_h = 68 * mm, 28 * mm
        box_x = right - box_w
        box_y = y - box_h
        c.setStrokeColorRGB(*red)
        c.setLineWidth(2.2)
        c.rect(box_x, box_y, box_w, box_h, stroke=1, fill=0)
        c.setFillColorRGB(*red)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(box_x + box_w / 2, box_y + box_h - 9 * mm, f"R.U.T.: {self._format_cl_rut(emisor_rut)}")
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(box_x + box_w / 2, box_y + box_h / 2 - 1 * mm, tipo_label)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(box_x + box_w / 2, box_y + 5 * mm, f"N° {folio}")
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(box_x + box_w / 2, box_y - 5 * mm, f"S.I.I. - {sii_office}")

        text_w = box_x - left - 6 * mm
        c.setFillColorRGB(*blue)
        c.setFont("Helvetica-Bold", 12)
        name_y = y - 2 * mm
        # wrap issuer name
        words = (emisor_name or "").upper().split()
        line = ""
        for w in words:
            test = f"{line} {w}".strip()
            if c.stringWidth(test, "Helvetica-Bold", 12) <= text_w:
                line = test
            else:
                c.drawString(left, name_y, line)
                name_y -= 5 * mm
                line = w
        if line:
            c.drawString(left, name_y, line)
            name_y -= 5 * mm
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 8)
        if emisor_giro:
            giro = emisor_giro.upper()
            while giro and c.stringWidth(giro, "Helvetica", 8) > text_w:
                giro = giro[:-1]
            c.drawString(left, name_y, giro)
            name_y -= 4 * mm
        if emisor_dir:
            c.drawString(left, name_y, emisor_dir[:90])
            name_y -= 4 * mm
        if emisor_contact:
            c.drawString(left, name_y, emisor_contact[:90])

        y = min(box_y - 12 * mm, name_y - 8 * mm)

        # ---- Receptor + fecha ----
        c.setFont("Helvetica-Bold", 9)
        labels = [
            ("R.U.T.", self._format_cl_rut(receptor_rut)),
            ("Razón social", receptor_name),
            ("Giro", receptor_giro.upper() if receptor_giro else ""),
            ("Dirección", receptor_dir),
            ("Contacto", receptor_contact),
        ]
        label_x = left
        value_x = left + 28 * mm
        row_y = y
        for lab, val in labels:
            if not val:
                continue
            c.setFont("Helvetica-Bold", 9)
            c.drawString(label_x, row_y, f"{lab} :")
            c.setFont("Helvetica", 9)
            c.drawString(value_x, row_y, str(val)[:78])
            row_y -= 4.5 * mm

        c.setFont("Helvetica", 9)
        c.drawRightString(right, y, self._format_cl_long_date(fch))
        c.drawRightString(right, y - 4.5 * mm, f"Venta: {venta}")
        y = row_y - 6 * mm

        # ---- Items table ----
        cols = [
            ("Item", 0.52),
            ("Cant.", 0.10),
            ("Unidad", 0.10),
            ("P. unitario", 0.14),
            ("Total item", 0.14),
        ]
        col_ws = [usable * r for _, r in cols]
        header_h = 7 * mm
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.8)
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(left, y - header_h, usable, header_h, stroke=1, fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 8)
        x = left
        for (title, _), w in zip(cols, col_ws):
            c.drawCentredString(x + w / 2, y - 4.8 * mm, title)
            x += w
        # vertical lines header
        x = left
        for w in col_ws[:-1]:
            x += w
            c.line(x, y, x, y - header_h)
        y -= header_h

        c.setFont("Helvetica", 8)
        for det in details:
            # estimate row height (2 lines for item)
            row_h = 9 * mm
            if y - row_h < 55 * mm:
                c.showPage()
                y = height - 20 * mm
            c.rect(left, y - row_h, usable, row_h, stroke=1, fill=0)
            x = left
            for w in col_ws[:-1]:
                x += w
                c.line(x, y, x, y - row_h)

            name = (det["name"] or "—")[:70]
            dsc = (det["dsc"] or name)[:70]
            c.setFont("Helvetica", 8)
            c.drawString(left + 1.5 * mm, y - 3.5 * mm, name)
            c.setFont("Helvetica", 7)
            c.drawString(left + 1.5 * mm, y - 7 * mm, dsc)
            c.setFont("Helvetica", 8)
            # qty
            x0 = left + col_ws[0]
            try:
                qty_f = float(det["qty"])
                qty_txt = f"{qty_f:.1f}".replace(".", ",")
            except (TypeError, ValueError):
                qty_txt = str(det["qty"])
            c.drawRightString(x0 + col_ws[1] - 1.5 * mm, y - 5 * mm, qty_txt)
            c.drawCentredString(x0 + col_ws[1] + col_ws[2] / 2, y - 5 * mm, str(det["unit"] or "Unid")[:8])
            c.drawRightString(
                x0 + col_ws[1] + col_ws[2] + col_ws[3] - 1.5 * mm,
                y - 5 * mm,
                self._format_cl_money(det["price"], 1),
            )
            c.drawRightString(right - 1.5 * mm, y - 5 * mm, self._format_cl_money(det["total"], 0))
            y -= row_h

        # ---- Footer: timbre + totales ----
        y -= 8 * mm
        footer_top = y
        timbre_w, timbre_h = 55 * mm, 32 * mm
        if ted_img is not None:
            c.drawImage(
                ted_img,
                left,
                footer_top - timbre_h,
                width=timbre_w,
                height=timbre_h,
                preserveAspectRatio=True,
                mask="auto",
            )
            c.setFont("Helvetica", 7)
            c.drawCentredString(left + timbre_w / 2, footer_top - timbre_h - 4 * mm, "Timbre Electrónico SII")
            c.drawCentredString(left + timbre_w / 2, footer_top - timbre_h - 7.5 * mm, "Resolución 80 de 2014")
            c.drawCentredString(
                left + timbre_w / 2,
                footer_top - timbre_h - 11 * mm,
                "Verifique documento: www.sii.cl",
            )
        else:
            c.setFont("Helvetica", 8)
            c.drawString(left, footer_top - 10 * mm, "Timbre Electrónico SII")
            c.drawString(left, footer_top - 14 * mm, "Verifique documento: www.sii.cl")

        totals = []
        if mnt_neto not in (None, ""):
            totals.append(("Neto $", self._format_cl_money(mnt_neto)))
        if mnt_exento not in (None, ""):
            totals.append(("Exento $", self._format_cl_money(mnt_exento)))
        if mnt_iva not in (None, ""):
            try:
                tasa_txt = f"{float(tasa_iva):.1f}"
            except (TypeError, ValueError):
                tasa_txt = str(tasa_iva)
            totals.append((f"IVA ({tasa_txt}%) $", self._format_cl_money(mnt_iva)))
        totals.append(("Total $", self._format_cl_money(mnt_total)))
        totals.append(("Valor a pagar $", self._format_cl_money(vlr_pagar)))

        # Totales a la derecha del timbre (como DTE profesional)
        c.setFillColorRGB(0, 0, 0)
        tot_y = footer_top - 4 * mm
        for lab, val in totals:
            c.setFont("Helvetica-Bold", 9)
            c.drawRightString(right - 30 * mm, tot_y, f"{lab} :")
            c.drawRightString(right, tot_y, val)
            tot_y -= 5.2 * mm

        # bottom line (no LibreDTE branding)
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.6)
        line_y = 14 * mm
        c.line(left, line_y, right, line_y)
        c.setFont("Helvetica", 7)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.drawString(left, line_y - 4 * mm, "Documento tributario electrónico")
        c.drawRightString(right, line_y - 4 * mm, "www.sii.cl")

        c.save()
        pdf = buf.getvalue()
        if not pdf.startswith(b"%PDF"):
            raise ValueError("PDF generado inválido")
        return pdf
