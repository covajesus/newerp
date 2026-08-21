from sqlalchemy.orm import Session
from sqlalchemy.dialects import mysql
from app.backend.db.models import ReceivedInboxModel, BranchOfficeModel
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
import requests

SIMPLEFACTURA_DOCUMENTS_RECEIVED_URL = "https://api.simplefactura.cl/documentsReceived"
SIMPLEFACTURA_CONSOLIDATE_RECEIVED_URL = "https://api.simplefactura.cl/documentsReceived/consolidate"
SIMPLEFACTURA_ACKNOWLEDGMENT_URL = "https://api.simplefactura.cl/acknowledgmentReceipt"
SIMPLEFACTURA_RECEIVED_TIMEOUT = int(os.getenv("SIMPLEFACTURA_RECEIVED_TIMEOUT", "45"))
SIMPLEFACTURA_CONSOLIDATE_MONTHS = int(os.getenv("SIMPLEFACTURA_CONSOLIDATE_MONTHS", "1"))
RECEIVED_INBOX_LOOKBACK_DAYS = int(os.getenv("RECEIVED_INBOX_LOOKBACK_DAYS", "30"))
RECEIVED_DTE_TYPES = (33, 34, 39, 61)
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
            existing_by_key[key] = row
            inserted += 1

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
                row.acknowledgment_status = "Accepted"
            else:
                row.status_id = RECEIVED_INBOX_STATUS_REJECTED
                row.acknowledgment_status = "Rejected"
            row.updated_date = now
            self.db.commit()
            return {
                "status": "success",
                "action": action,
                "id": row.id,
                "simplefactura": body,
            }
        except Exception as exc:
            self.db.rollback()
            return {"status": "error", "message": str(exc)}
