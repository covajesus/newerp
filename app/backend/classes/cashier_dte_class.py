"""DTE de cajas (tabla dtes en DB2) — consulta y PDF (SimpleFactura → LibreDTE)."""
import base64
import uuid
from datetime import datetime

import requests
from sqlalchemy import desc, func, or_, text
from sqlalchemy.orm import Session

from app.backend.classes.customer_ticket_class import CustomerTicketClass
from app.backend.classes.file_class import FileClass
from app.backend.classes.setting_class import SettingClass
from app.backend.db.models import BranchOfficeModel, CashierModel, DteModel

LIBREDTE_TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
LIBREDTE_RUT_EMISOR = "76063822-6"


class CashierDteClass:
    def __init__(self, db2: Session, db_main: Session):
        self.db2 = db2
        self.db_main = db_main
        self.file_class = FileClass(db_main)

    def _cashier_ids_for_branch(self, branch_office_id: int) -> list[int]:
        """IDs de caja de la sucursal (DB2, con fallback a DB1)."""
        bid = int(branch_office_id)
        ids = [
            int(r[0])
            for r in self.db2.query(CashierModel.id)
            .filter(CashierModel.branch_office_id == bid)
            .all()
        ]
        if ids:
            return ids
        return [
            int(r[0])
            for r in self.db_main.query(CashierModel.id)
            .filter(CashierModel.branch_office_id == bid)
            .all()
        ]

    def search(
        self,
        *,
        branch_office_id=None,
        folio=None,
        amount=None,
        since=None,
        until=None,
        page=1,
        items_per_page=10,
    ):
        try:
            filters = [
                DteModel.dte_type_id == 39,
                DteModel.folio.isnot(None),
                DteModel.folio > 0,
            ]

            cashier_ids: list[int] = []
            if branch_office_id is not None:
                bid = int(branch_office_id)
                cashier_ids = self._cashier_ids_for_branch(bid)
                # Algunas cajas (p. ej. Cordillera) guardan mal/null branch_office_id
                # en dtes pero sí el cashier_id correcto.
                if cashier_ids:
                    filters.append(
                        or_(
                            DteModel.branch_office_id == bid,
                            DteModel.cashier_id.in_(cashier_ids),
                        )
                    )
                else:
                    filters.append(DteModel.branch_office_id == bid)
            if folio is not None:
                filters.append(DteModel.folio == int(folio))
            if amount is not None:
                filters.append(DteModel.total == int(amount))
            if since:
                filters.append(func.date(DteModel.added_date) >= since)
            if until:
                filters.append(func.date(DteModel.added_date) <= until)

            query = (
                self.db2.query(
                    DteModel.id,
                    DteModel.branch_office_id,
                    DteModel.cashier_id,
                    DteModel.folio,
                    DteModel.total,
                    DteModel.cash_amount,
                    DteModel.card_amount,
                    DteModel.added_date,
                    DteModel.rut,
                    DteModel.entrance_hour,
                    DteModel.exit_hour,
                    DteModel.dte_type_id,
                    DteModel.status_id,
                    BranchOfficeModel.branch_office,
                    CashierModel.cashier,
                )
                .outerjoin(
                    BranchOfficeModel,
                    BranchOfficeModel.id == DteModel.branch_office_id,
                )
                .outerjoin(CashierModel, CashierModel.id == DteModel.cashier_id)
                .filter(*filters)
                .order_by(desc(DteModel.added_date), desc(DteModel.id))
            )

            total_items = query.count()
            if total_items == 0:
                # Fallback: folios usados/facturados en DB2 (sin fila en dtes).
                # Caso típico sucursales nuevas como LIDER CORDILLERA.
                # Sin monto: los folios DB2 no guardan total.
                if amount is None and (
                    branch_office_id is not None or folio is not None or since or until
                ):
                    return self._search_from_used_folios(
                        branch_office_id=branch_office_id,
                        folio=folio,
                        since=since,
                        until=until,
                        page=page,
                        items_per_page=items_per_page,
                        cashier_ids=cashier_ids,
                    )
                return {
                    "total_items": 0,
                    "total_pages": 0,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": [],
                }

            total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
            if page < 1:
                page = 1
            if page > total_pages:
                page = total_pages

            rows = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

            data = []
            for row in rows:
                folio_n = row.folio
                have_credit_note = 0
                if folio_n:
                    nc_count = (
                        self.db2.query(DteModel.id)
                        .filter(
                            DteModel.dte_type_id == 61,
                            DteModel.denied_folio == str(folio_n),
                        )
                        .count()
                    )
                    have_credit_note = 1 if nc_count > 0 else 0

                data.append(
                    {
                        "id": row.id,
                        "rut": row.rut,
                        "branch_office_id": row.branch_office_id,
                        "cashier_id": row.cashier_id,
                        "cashier": row.cashier,
                        "entrance_hour": row.entrance_hour,
                        "exit_hour": row.exit_hour,
                        "dte_type_id": row.dte_type_id,
                        "folio": row.folio,
                        "total": row.total,
                        "cash_amount": row.cash_amount,
                        "card_amount": row.card_amount,
                        "status_id": row.status_id,
                        "added_date": row.added_date.strftime("%d-%m-%Y %H:%M")
                        if row.added_date
                        else None,
                        "branch_office": row.branch_office,
                        "have_credit_note": have_credit_note,
                        "source": "dtes",
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
            return {"status": "error", "message": str(e)}

    def _search_from_used_folios(
        self,
        *,
        branch_office_id=None,
        folio=None,
        since=None,
        until=None,
        page=1,
        items_per_page=10,
        cashier_ids=None,
    ):
        """Lista boletas desde folios DB2 usados/facturados cuando no hay filas en dtes."""
        where = [
            "f.folio IS NOT NULL",
            "f.folio > 0",
            "(COALESCE(f.used_status_id, 0) = 1 OR COALESCE(f.billed_status_id, 0) = 1)",
        ]
        params: dict = {}

        if folio is not None:
            where.append("f.folio = :folio")
            params["folio"] = int(folio)

        if branch_office_id is not None:
            bid = int(branch_office_id)
            cids = cashier_ids or self._cashier_ids_for_branch(bid)
            if cids:
                placeholders = ", ".join(f":c{i}" for i in range(len(cids)))
                where.append(
                    f"(f.branch_office_id = :bid OR f.cashier_id IN ({placeholders}))"
                )
                params["bid"] = bid
                for i, cid in enumerate(cids):
                    params[f"c{i}"] = int(cid)
            else:
                where.append("f.branch_office_id = :bid")
                params["bid"] = bid

        if since:
            where.append("DATE(COALESCE(f.updated_date, f.added_date)) >= :since")
            params["since"] = since
        if until:
            where.append("DATE(COALESCE(f.updated_date, f.added_date)) <= :until")
            params["until"] = until

        where_sql = " AND ".join(where)
        count_row = self.db2.execute(
            text(f"SELECT COUNT(*) AS total FROM folios f WHERE {where_sql}"),
            params,
        ).mappings().first()
        total_items = int(count_row["total"] if count_row else 0)
        if total_items == 0:
            return {
                "total_items": 0,
                "total_pages": 0,
                "current_page": page,
                "items_per_page": items_per_page,
                "data": [],
            }

        total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages
        offset = (page - 1) * items_per_page

        rows = self.db2.execute(
            text(
                f"""
                SELECT
                    f.folio,
                    f.branch_office_id,
                    f.cashier_id,
                    COALESCE(f.updated_date, f.added_date) AS folio_date,
                    bo.branch_office,
                    c.cashier
                FROM folios f
                LEFT JOIN branch_offices bo ON bo.id = f.branch_office_id
                LEFT JOIN cashiers c ON c.id = f.cashier_id
                WHERE {where_sql}
                ORDER BY COALESCE(f.updated_date, f.added_date) DESC, f.folio DESC
                LIMIT :limit_n OFFSET :offset_n
                """
            ),
            {**params, "limit_n": int(items_per_page), "offset_n": int(offset)},
        ).mappings().all()

        # Nombres de sucursal/caja desde DB1 si DB2 no los trae
        branch_name = None
        if branch_office_id is not None:
            bo = (
                self.db_main.query(BranchOfficeModel.branch_office)
                .filter(BranchOfficeModel.id == int(branch_office_id))
                .first()
            )
            branch_name = bo[0] if bo else None

        data = []
        for row in rows:
            folio_n = int(row["folio"])
            folio_date = row["folio_date"]
            data.append(
                {
                    "id": None,
                    "rut": None,
                    "branch_office_id": row["branch_office_id"],
                    "cashier_id": row["cashier_id"],
                    "cashier": row["cashier"],
                    "entrance_hour": None,
                    "exit_hour": None,
                    "dte_type_id": 39,
                    "folio": folio_n,
                    "total": None,
                    "cash_amount": None,
                    "card_amount": None,
                    "status_id": None,
                    "added_date": folio_date.strftime("%d-%m-%Y %H:%M")
                    if folio_date
                    else None,
                    "branch_office": row["branch_office"] or branch_name,
                    "have_credit_note": 0,
                    "source": "folios",
                }
            )

        return {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page,
            "items_per_page": items_per_page,
            "data": data,
        }

    def _simplefactura_bearer_token(self) -> str | None:
        ticket_cls = CustomerTicketClass(self.db_main)
        forced = ticket_cls._v2_bearer_token()[0]  # noqa: SLF001 — mismo token que emisión v2
        if forced:
            return forced
        setting_data = SettingClass(self.db_main).get()
        return (setting_data.get("setting_data") or {}).get("simplefactura_token")

    def _db2_dte_for_pdf(self, dte_id: int):
        """DB2 `dtes` no tiene category_id ni otras columnas del ERP principal."""
        return (
            self.db2.query(DteModel.id, DteModel.folio, DteModel.dte_type_id)
            .filter(DteModel.id == dte_id)
            .first()
        )

    def _encode_pdf_response(self, pdf_content: bytes, folio: int):
        if not pdf_content or not pdf_content.startswith(b"%PDF"):
            return {
                "status": "error",
                "message": "Respuesta no es un PDF válido",
            }
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_filename = f"boleta_caja_{folio}_{timestamp}_{uuid.uuid4().hex[:8]}.pdf"
        remote_path = unique_filename
        self.file_class.temporal_upload(pdf_content, remote_path)
        file_contents = self.file_class.download(remote_path)
        encoded_file = base64.b64encode(file_contents).decode("utf-8")
        self.file_class.delete(remote_path)
        return {
            "status": "success",
            "file_name": unique_filename,
            "file_data": encoded_file,
        }

    def _pdf_from_simplefactura(self, folio: int, dte_type_id: int = 39):
        token = self._simplefactura_bearer_token()
        if not token:
            return {"status": "error", "message": "No hay token SimpleFactura configurado"}

        payload = {
            "credenciales": {
                "rutEmisor": "76063822-6",
                "nombreSucursal": "Casa Matriz",
            },
            "dteReferenciadoExterno": {
                "folio": int(folio),
                "codigoTipoDte": int(dte_type_id),
                "ambiente": 1,
            },
        }
        url = "https://api.simplefactura.cl/getPdf"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
        except requests.RequestException as exc:
            return {"status": "error", "message": f"Error al conectar con SimpleFactura: {exc}"}

        if response.status_code == 401:
            try:
                token = CustomerTicketClass(self.db_main).fetch_simplefactura_token_from_jisbackend()
                response = requests.post(
                    url,
                    json=payload,
                    headers={**headers, "Authorization": f"Bearer {token}"},
                    timeout=30,
                )
            except (ValueError, requests.RequestException) as exc:
                return {"status": "error", "message": f"No se pudo refrescar token: {exc}"}

        if (
            response.status_code != 200
            or not response.content
            or not response.content.startswith(b"%PDF")
        ):
            return {
                "status": "error",
                "message": f"SimpleFactura getPdf HTTP {response.status_code}",
                "detail": (response.text or "")[:300],
            }

        return self._encode_pdf_response(response.content, int(folio))

    def _pdf_from_libredte(self, folio: int, dte_type_id: int = 39):
        """Fallback para boletas de caja emitidas por LibreDTE (p.ej. Cordillera)."""
        url = (
            f"https://libredte.cl/api/dte/dte_emitidos/pdf/{int(dte_type_id)}/"
            f"{int(folio)}/{LIBREDTE_RUT_EMISOR}?formato=general&papelContinuo=0"
            f"&copias_tributarias=1&copias_cedibles=1&cedible=0&compress=0&base64=0"
        )
        try:
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {LIBREDTE_TOKEN}",
                    "Content-Type": "application/json",
                    "Accept": "application/pdf, application/octet-stream, */*",
                },
                timeout=60,
            )
        except requests.RequestException as exc:
            return {"status": "error", "message": f"Error al conectar con LibreDTE: {exc}"}

        if (
            response.status_code != 200
            or not response.content
            or not response.content.startswith(b"%PDF")
        ):
            return {
                "status": "error",
                "message": f"LibreDTE pdf HTTP {response.status_code}",
                "detail": (response.text or "")[:300],
            }

        return self._encode_pdf_response(response.content, int(folio))

    def _download_pdf_with_fallbacks(self, folio: int, dte_type_id: int = 39):
        errors = []
        for tipo in (int(dte_type_id or 39), 39, 33):
            sf = self._pdf_from_simplefactura(int(folio), tipo)
            if sf.get("status") == "success":
                sf["source"] = "simplefactura"
                return sf
            errors.append(f"SF tipo={tipo}: {sf.get('message')} {sf.get('detail') or ''}".strip())

            ldte = self._pdf_from_libredte(int(folio), tipo)
            if ldte.get("status") == "success":
                ldte["source"] = "libredte"
                return ldte
            errors.append(
                f"LibreDTE tipo={tipo}: {ldte.get('message')} {ldte.get('detail') or ''}".strip()
            )

        return {
            "status": "error",
            "message": (
                f"No se encontró PDF del folio {folio} en SimpleFactura ni LibreDTE"
            ),
            "detail": " | ".join(errors)[:800],
        }

    def download_pdf(self, dte_id: int):
        row = self._db2_dte_for_pdf(dte_id)
        if not row or not row.folio:
            return {"status": "error", "message": "DTE no encontrado o sin folio"}
        return self._download_pdf_with_fallbacks(
            int(row.folio), int(row.dte_type_id or 39)
        )

    def download_pdf_by_folio(self, folio: int, dte_type_id: int = 39):
        """PDF directo por folio (cuando no hay fila en dtes de DB2)."""
        if not folio or int(folio) <= 0:
            return {"status": "error", "message": "Folio inválido"}
        # Preferir tipo/dte local si existe
        row = (
            self.db2.query(DteModel.id, DteModel.folio, DteModel.dte_type_id)
            .filter(DteModel.folio == int(folio))
            .order_by(desc(DteModel.id))
            .first()
        )
        tipo = int(row.dte_type_id) if row and row.dte_type_id else int(dte_type_id)
        return self._download_pdf_with_fallbacks(int(folio), tipo)
