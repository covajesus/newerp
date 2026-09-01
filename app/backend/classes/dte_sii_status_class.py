"""Sincroniza estado SII de DTE emitidos vía SimpleFactura (documentsIssued).

sii_status_id:
  1 = Pendiente
  2 = Aceptado
  3 = Rechazado
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Optional

import requests
from sqlalchemy import or_, text
from sqlalchemy.orm import Session

from app.backend.classes.customer_ticket_class import (
    CustomerTicketClass,
    SIMPLEFACTURA_AMBIENTE,
    SIMPLEFACTURA_RUT_EMISOR,
    SIMPLEFACTURA_SUCURSAL,
    is_document_simplefactura_v2,
)
from app.backend.classes.log_class import LogClass
from app.backend.db.models import DteModel

SII_STATUS_PENDING = 1
SII_STATUS_ACCEPTED = 2
SII_STATUS_REJECTED = 3

SII_STATUS_LABELS = {
    SII_STATUS_PENDING: "Pendiente",
    SII_STATUS_ACCEPTED: "Aceptado",
    SII_STATUS_REJECTED: "Rechazado",
}

SIMPLEFACTURA_DOCUMENTS_ISSUED_URL = "https://api.simplefactura.cl/documentsIssued"
# Mes completo suele timeout; por defecto 120s y ventanas cortas.
SIMPLEFACTURA_ISSUED_TIMEOUT = int(os.getenv("SIMPLEFACTURA_ISSUED_TIMEOUT", "120"))
DTE_SII_SYNC_LOOKBACK_DAYS = int(os.getenv("DTE_SII_SYNC_LOOKBACK_DAYS", "90"))
# Días por request a documentsIssued. 1 = estable (mes entero timeout en SF).
DTE_SII_SYNC_CHUNK_DAYS = int(os.getenv("DTE_SII_SYNC_CHUNK_DAYS", "1"))
# Tope por invocación de cron (Apache ~5–15 min). El siguiente tick continúa.
DTE_SII_SYNC_MAX_SECONDS = int(os.getenv("DTE_SII_SYNC_MAX_SECONDS", "180"))
DTE_SII_EMITTED_TYPES = (33, 39, 61)


def serialize_dte_sii_fields(dte) -> dict:
    """Campos SII para respuestas de listado."""
    status_id = getattr(dte, "sii_status_id", None)
    checked = getattr(dte, "sii_status_checked_at", None)
    return {
        "sii_status_id": status_id,
        "sii_status_label": SII_STATUS_LABELS.get(int(status_id)) if status_id else None,
        "sii_track_id": getattr(dte, "sii_track_id", None),
        "sii_rejection_reason": getattr(dte, "sii_rejection_reason", None),
        "sii_status_checked_at": checked.strftime("%Y-%m-%d %H:%M:%S") if checked else None,
    }


def mark_dte_sii_pending(dte) -> None:
    """Al emitir por SimpleFactura: estado SII pendiente."""
    if dte is None:
        return
    dte.sii_status_id = SII_STATUS_PENDING
    dte.sii_rejection_reason = None
    dte.sii_status_checked_at = None
    dte.sii_status_alerted_at = None


class DteSiiStatusClass:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _sf_item_value(item: dict, *keys):
        for key in keys:
            if key in item and item.get(key) not in (None, ""):
                return item.get(key)
        lower_map = {str(k).lower(): v for k, v in item.items()}
        for key in keys:
            val = lower_map.get(str(key).lower())
            if val not in (None, ""):
                return val
        return None

    @staticmethod
    def _extract_list(body: Any) -> list:
        if isinstance(body, list):
            return [x for x in body if isinstance(x, dict)]
        if not isinstance(body, dict):
            return []
        for key in ("data", "Data", "items", "Items", "result", "Result", "documentos", "Documentos"):
            val = body.get(key)
            if isinstance(val, list):
                return [x for x in val if isinstance(x, dict)]
            if isinstance(val, dict):
                for nested_key in ("items", "Items", "data", "Data", "list", "List"):
                    nested = val.get(nested_key)
                    if isinstance(nested, list):
                        return [x for x in nested if isinstance(x, dict)]
        return []

    @staticmethod
    def map_sii_status(raw_status: str | None, raw_detail: str | None = None) -> tuple[int, str | None]:
        """Normaliza texto SimpleFactura/SII → (sii_status_id, motivo)."""
        text_all = " ".join(
            str(x).strip() for x in (raw_status, raw_detail) if x not in (None, "")
        ).strip()
        lower = text_all.lower()
        if not lower:
            return SII_STATUS_PENDING, None

        if any(
            token in lower
            for token in (
                "rechaz",
                "rch",
                "rejected",
                "no conforme",
                "reparo",
                "rpr",
            )
        ):
            return SII_STATUS_REJECTED, text_all[:2000]

        if any(
            token in lower
            for token in (
                "aceptad",
                "dok",
                "ok",
                "conforme",
                "aprobad",
                "aceptado",
            )
        ):
            return SII_STATUS_ACCEPTED, None

        return SII_STATUS_PENDING, text_all[:2000] if text_all else None

    def _simplefactura_token(self) -> str:
        ticket_class = CustomerTicketClass(self.db)
        forced = (os.getenv("DTE_V2_FORCE_TOKEN") or os.getenv("SIMPLEFACTURA_FORCE_TOKEN") or "").strip()
        if forced:
            return forced
        result = ticket_class.get_token()
        if result.get("status") != "success":
            raise ValueError(result.get("message") or "No se pudo obtener token SimpleFactura")
        token = result.get("accessToken")
        if not token:
            raise ValueError("Token SimpleFactura vacío")
        return token

    def _simplefactura_post(self, payload: dict) -> Any:
        token = self._simplefactura_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(
                SIMPLEFACTURA_DOCUMENTS_ISSUED_URL,
                json=payload,
                headers=headers,
                timeout=SIMPLEFACTURA_ISSUED_TIMEOUT,
            )
        except requests.Timeout as exc:
            raise ValueError(
                f"SimpleFactura documentsIssued timeout ({SIMPLEFACTURA_ISSUED_TIMEOUT}s)"
            ) from exc
        except requests.RequestException as exc:
            raise ValueError(f"SimpleFactura connection error: {exc}") from exc

        if response.status_code == 401:
            token = CustomerTicketClass(self.db).fetch_simplefactura_token_from_jisbackend()
            headers["Authorization"] = f"Bearer {token}"
            response = requests.post(
                SIMPLEFACTURA_DOCUMENTS_ISSUED_URL,
                json=payload,
                headers=headers,
                timeout=SIMPLEFACTURA_ISSUED_TIMEOUT,
            )

        if response.status_code != 200:
            raise ValueError(
                f"SimpleFactura documentsIssued HTTP {response.status_code}: "
                f"{(response.text or '')[:400]}"
            )
        try:
            return response.json()
        except ValueError as exc:
            raise ValueError(f"SimpleFactura documentsIssued: JSON inválido ({exc})") from exc

    def _fetch_issued(
        self,
        *,
        dte_type_id: int,
        since: str,
        until: str,
        folio: int = 0,
    ) -> list[dict]:
        payload = {
            "credenciales": {
                "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
                "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
                "emailUsuario": None,
                "rutContribuyente": None,
            },
            "ambiente": SIMPLEFACTURA_AMBIENTE,
            "folio": int(folio or 0),
            "codigoTipoDte": int(dte_type_id),
            "desde": since,
            "hasta": until,
            "rutEmisor": None,
        }
        body = self._simplefactura_post(payload)
        return self._extract_list(body)

    def _parse_item(self, item: dict) -> dict:
        folio_raw = self._sf_item_value(item, "folio", "Folio")
        try:
            folio = int(folio_raw) if folio_raw is not None else None
        except (TypeError, ValueError):
            folio = None

        tipo_raw = self._sf_item_value(
            item, "codigoTipoDte", "CodigoTipoDte", "tipoDte", "TipoDte", "dte", "DTE"
        )
        try:
            dte_type_id = int(tipo_raw) if tipo_raw is not None else None
        except (TypeError, ValueError):
            dte_type_id = None

        track_raw = self._sf_item_value(item, "trackId", "TrackId", "track_id", "TrackID")
        try:
            track_id = int(track_raw) if track_raw not in (None, "") else None
        except (TypeError, ValueError):
            track_id = None

        estado = str(
            self._sf_item_value(item, "estadoSII", "EstadoSII", "respuesta", "Respuesta", "estado", "Estado")
            or ""
        ).strip()
        detail = str(
            self._sf_item_value(
                item,
                "glosa",
                "Glosa",
                "mensaje",
                "Mensaje",
                "detalle",
                "Detalle",
                "motivo",
                "Motivo",
            )
            or ""
        ).strip() or None

        status_id, reason = self.map_sii_status(estado, detail)
        if status_id != SII_STATUS_REJECTED:
            reason = detail if status_id == SII_STATUS_PENDING and detail else None
        elif not reason:
            reason = estado or detail

        return {
            "folio": folio,
            "dte_type_id": dte_type_id,
            "sii_status_id": status_id,
            "sii_track_id": track_id,
            "sii_rejection_reason": reason if status_id == SII_STATUS_REJECTED else None,
            "raw_estado": estado or None,
        }

    def _candidates_query(self, *, dte_id: Optional[int] = None, lookback_days: Optional[int] = None):
        days = lookback_days if lookback_days is not None else DTE_SII_SYNC_LOOKBACK_DAYS
        since = datetime.now() - timedelta(days=max(1, days))
        q = self.db.query(DteModel).filter(
            DteModel.folio.isnot(None),
            DteModel.folio > 0,
            DteModel.dte_type_id.in_(DTE_SII_EMITTED_TYPES),
            DteModel.status_id.in_([4, 5, 14, 16]),
            or_(
                DteModel.sii_status_id.is_(None),
                DteModel.sii_status_id == SII_STATUS_PENDING,
                DteModel.added_date >= since,
            ),
        )
        if dte_id:
            q = q.filter(DteModel.id == int(dte_id))
        else:
            q = q.filter(or_(DteModel.added_date >= since, DteModel.sii_status_id == SII_STATUS_PENDING))
        return q.order_by(DteModel.id.desc())

    def _is_simplefactura_candidate(self, dte) -> bool:
        try:
            return bool(is_document_simplefactura_v2(self.db, dte))
        except Exception:
            # NC 61: si el original o el propio folio está en pool
            dte_id = getattr(dte, "id", None)
            if not dte_id:
                return False
            row = self.db.execute(
                text(
                    "SELECT 1 FROM folios "
                    "WHERE dte_id = :dte_id AND dte_id > 0 AND document_type_id IN (33, 39, 61) "
                    "LIMIT 1"
                ),
                {"dte_id": int(dte_id)},
            ).first()
            return bool(row)

    def _apply_parsed(self, dte: DteModel, parsed: dict) -> dict:
        prev = int(dte.sii_status_id) if dte.sii_status_id is not None else None
        now = datetime.now()
        dte.sii_status_id = int(parsed["sii_status_id"])
        if parsed.get("sii_track_id") is not None:
            dte.sii_track_id = int(parsed["sii_track_id"])
        dte.sii_rejection_reason = parsed.get("sii_rejection_reason")
        dte.sii_status_checked_at = now
        dte.updated_date = now

        alerted = False
        if (
            dte.sii_status_id == SII_STATUS_REJECTED
            and prev != SII_STATUS_REJECTED
            and dte.sii_status_alerted_at is None
        ):
            self._alert_rejected(dte)
            dte.sii_status_alerted_at = now
            alerted = True

        self.db.add(dte)
        return {
            "id": dte.id,
            "folio": dte.folio,
            "dte_type_id": dte.dte_type_id,
            "prev_sii_status_id": prev,
            "sii_status_id": dte.sii_status_id,
            "sii_track_id": dte.sii_track_id,
            "sii_rejection_reason": dte.sii_rejection_reason,
            "alerted": alerted,
        }

    def _alert_rejected(self, dte: DteModel) -> None:
        msg = (
            f"DTE tipo {dte.dte_type_id} folio {dte.folio} rechazado por el SII "
            f"(RUT {dte.rut or 'n/a'})"
        )
        detail = dte.sii_rejection_reason or ""
        if dte.sii_track_id:
            detail = f"track_id={dte.sii_track_id}; {detail}".strip("; ")
        try:
            LogClass(self.db).log_error(
                "dte_sii_rejected",
                msg,
                reference_type="dte",
                reference_id=dte.id,
                error_code="sii_rejected",
                detail=detail or None,
                process_name="DTE - Rechazado SII",
            )
        except Exception as exc:
            print(f"[dte_sii_status] Slack/log failed: {exc}", flush=True)

    def _pending_sii_query(self, lookback_days: Optional[int] = None):
        """DTE SimpleFactura emitidos con sii_status_id=1 (Pendiente) en ventana lookback."""
        days = lookback_days if lookback_days is not None else 30
        since = datetime.now() - timedelta(days=max(1, days))
        return (
            self.db.query(DteModel)
            .filter(
                DteModel.folio.isnot(None),
                DteModel.folio > 0,
                DteModel.dte_type_id.in_(DTE_SII_EMITTED_TYPES),
                DteModel.status_id.in_([4, 5, 14, 16]),
                DteModel.sii_status_id == SII_STATUS_PENDING,
                DteModel.added_date >= since,
            )
            .order_by(DteModel.id.asc())
        )

    def _sync_dte_entity(self, dte: DteModel, *, commit: bool = True) -> dict:
        """Consulta SimpleFactura por folio (documentsIssued) y actualiza el DTE."""
        if not dte.folio or int(dte.folio) <= 0:
            return {"status": "error", "message": "DTE sin folio emitido", "id": dte.id}
        if not self._is_simplefactura_candidate(dte):
            return {
                "status": "skipped",
                "message": "DTE no emitido por SimpleFactura; sync SII solo aplica a SF",
                "id": dte.id,
            }

        added = dte.added_date or datetime.now()
        since = (added - timedelta(days=3)).strftime("%Y-%m-%d")
        until = (added + timedelta(days=3)).strftime("%Y-%m-%d")
        try:
            items = self._fetch_issued(
                dte_type_id=int(dte.dte_type_id or 0),
                since=since,
                until=until,
                folio=int(dte.folio),
            )
        except Exception as exc:
            return {"status": "error", "message": str(exc), "id": dte.id}

        parsed = None
        for item in items:
            p = self._parse_item(item)
            if p.get("folio") == int(dte.folio):
                if p.get("dte_type_id") in (None, int(dte.dte_type_id or 0)):
                    parsed = p
                    break
        if not parsed and items:
            for item in items:
                p = self._parse_item(item)
                if p.get("folio") == int(dte.folio):
                    parsed = p
                    break

        if not parsed:
            dte.sii_status_id = dte.sii_status_id or SII_STATUS_PENDING
            dte.sii_status_checked_at = datetime.now()
            self.db.add(dte)
            if commit:
                self.db.commit()
            return {
                "status": "success",
                "message": "Sin registro en SimpleFactura documentsIssued; queda Pendiente",
                "id": dte.id,
                "folio": dte.folio,
                "dte_type_id": dte.dte_type_id,
                "prev_sii_status_id": SII_STATUS_PENDING,
                "sii_status_id": dte.sii_status_id,
            }

        result = self._apply_parsed(dte, parsed)
        if commit:
            self.db.commit()
        return {"status": "success", **result, **serialize_dte_sii_fields(dte)}

    def sync_one(self, dte_id: int) -> dict:
        dte = self.db.query(DteModel).filter(DteModel.id == int(dte_id)).first()
        if not dte:
            return {"status": "error", "message": "DTE no encontrado"}
        return self._sync_dte_entity(dte, commit=True)

    def _date_chunks(self, start: datetime, end: datetime, chunk_days: int) -> list[tuple[str, str]]:
        """Particiones inclusive [start, end] en ventanas de chunk_days."""
        days = max(1, int(chunk_days))
        chunks: list[tuple[str, str]] = []
        cursor = start.date()
        end_date = end.date()
        while cursor <= end_date:
            chunk_end = min(cursor + timedelta(days=days - 1), end_date)
            chunks.append((cursor.strftime("%Y-%m-%d"), chunk_end.strftime("%Y-%m-%d")))
            cursor = chunk_end + timedelta(days=1)
        return chunks

    def _fetch_issued_resilient(
        self,
        *,
        dte_type_id: int,
        since: str,
        until: str,
        errors: list,
    ) -> list[dict]:
        """documentsIssued por rango; si timeout, parte en días y luego deja el error."""
        try:
            return self._fetch_issued(dte_type_id=dte_type_id, since=since, until=until, folio=0)
        except Exception as exc:
            msg = str(exc)
            # Reintentar día a día solo si el rango es > 1 día
            try:
                start = datetime.strptime(since, "%Y-%m-%d")
                end = datetime.strptime(until, "%Y-%m-%d")
            except ValueError:
                errors.append(f"tipo={dte_type_id} {since}..{until}: {msg}")
                return []
            if (end - start).days <= 0:
                errors.append(f"tipo={dte_type_id} {since}..{until}: {msg}")
                return []

            collected: list[dict] = []
            day_errors = 0
            for day_since, day_until in self._date_chunks(start, end, 1):
                try:
                    collected.extend(
                        self._fetch_issued(
                            dte_type_id=dte_type_id,
                            since=day_since,
                            until=day_until,
                            folio=0,
                        )
                    )
                except Exception as day_exc:
                    day_errors += 1
                    errors.append(f"tipo={dte_type_id} {day_since}: {day_exc}")
            if day_errors and not collected:
                errors.append(
                    f"tipo={dte_type_id} {since}..{until}: fallback diario falló ({msg})"
                )
            return collected

    def _fetch_one_folio(self, dte: DteModel) -> dict | None:
        added = dte.added_date or datetime.now()
        since = (added - timedelta(days=3)).strftime("%Y-%m-%d")
        until = (added + timedelta(days=3)).strftime("%Y-%m-%d")
        items = self._fetch_issued(
            dte_type_id=int(dte.dte_type_id or 0),
            since=since,
            until=until,
            folio=int(dte.folio),
        )
        for item in items:
            parsed = self._parse_item(item)
            if parsed.get("folio") == int(dte.folio):
                if parsed.get("dte_type_id") in (None, int(dte.dte_type_id or 0)):
                    return parsed
        for item in items:
            parsed = self._parse_item(item)
            if parsed.get("folio") == int(dte.folio):
                return parsed
        return None

    def sync(
        self,
        *,
        lookback_days: Optional[int] = None,
        limit: int = 5,
        max_seconds: Optional[int] = None,
    ) -> dict:
        """Cron: recorre uno a uno DTE con sii_status_id=1 (Pendiente), últimos N días.

        Cada fila usa el mismo fetch por folio que sync_one (~10s c/u).
        limit = cuántos procesar por tick; max_seconds = tope de tiempo del request.
        """
        import time

        started = time.monotonic()
        budget = max_seconds if max_seconds is not None else DTE_SII_SYNC_MAX_SECONDS
        lookback = lookback_days if lookback_days is not None else 30
        batch_limit = max(1, int(limit))
        # Reserva ~12s por folio antes de iniciar otro
        per_dte_reserve = 12

        summary = {
            "status": "success",
            "mode": "one_by_one",
            "processed": 0,
            "checked": 0,
            "updated": 0,
            "still_pending": 0,
            "rejected_alerts": 0,
            "skipped": 0,
            "errors": [],
            "items": [],
            "has_more": False,
            "lookback_days": lookback,
            "elapsed_seconds": 0,
            "pending_remaining": 0,
        }

        def over_budget() -> bool:
            return (time.monotonic() - started) >= max(15, int(budget) - per_dte_reserve)

        # Traer más filas por si algunas no son SimpleFactura
        candidates = self._pending_sii_query(lookback).limit(batch_limit + 200).all()

        for dte in candidates:
            if summary["processed"] >= batch_limit:
                summary["has_more"] = True
                break
            if over_budget():
                summary["has_more"] = True
                break

            if not self._is_simplefactura_candidate(dte):
                summary["skipped"] += 1
                continue

            summary["checked"] += 1
            try:
                result = self._sync_dte_entity(dte, commit=True)
                summary["processed"] += 1

                st = result.get("status")
                if st == "skipped":
                    summary["skipped"] += 1
                elif st == "error":
                    summary["errors"].append(
                        f"dte_id={dte.id} folio={dte.folio}: {result.get('message')}"
                    )
                elif st == "success":
                    prev = result.get("prev_sii_status_id", SII_STATUS_PENDING)
                    new = result.get("sii_status_id")
                    if new == SII_STATUS_PENDING:
                        summary["still_pending"] += 1
                    elif new != prev:
                        summary["updated"] += 1
                    if result.get("alerted"):
                        summary["rejected_alerts"] += 1
                    if len(summary["items"]) < 50:
                        summary["items"].append(
                            {
                                "id": result.get("id"),
                                "folio": result.get("folio"),
                                "dte_type_id": result.get("dte_type_id"),
                                "prev_sii_status_id": prev,
                                "sii_status_id": new,
                            }
                        )
            except Exception as exc:
                summary["errors"].append(f"dte_id={dte.id} folio={dte.folio}: {exc}")

        pending_remaining = self._pending_sii_query(lookback).count()
        summary["pending_remaining"] = pending_remaining
        if pending_remaining > 0:
            summary["has_more"] = True

        if summary["errors"] and summary["processed"] == 0 and not summary["has_more"]:
            summary["status"] = "error"
        elif summary["errors"]:
            summary["status"] = "partial"
        summary["elapsed_seconds"] = round(time.monotonic() - started, 1)
        return summary
