"""DTE de cajas (tabla dtes en DB2) — consulta y PDF vía SimpleFactura getPdf."""
import base64
import uuid
from datetime import datetime

import requests
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.backend.classes.customer_ticket_class import CustomerTicketClass
from app.backend.classes.file_class import FileClass
from app.backend.classes.setting_class import SettingClass
from app.backend.db.models import BranchOfficeModel, CashierModel, DteModel


class CashierDteClass:
    def __init__(self, db2: Session, db_main: Session):
        self.db2 = db2
        self.db_main = db_main
        self.file_class = FileClass(db_main)

    def search(
        self,
        *,
        branch_office_id=None,
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

            if branch_office_id is not None:
                filters.append(DteModel.branch_office_id == int(branch_office_id))
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
                folio = row.folio
                have_credit_note = 0
                if folio:
                    nc_count = (
                        self.db2.query(DteModel.id)
                        .filter(
                            DteModel.dte_type_id == 61,
                            DteModel.denied_folio == str(folio),
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

    def _simplefactura_bearer_token(self) -> str | None:
        ticket_cls = CustomerTicketClass(self.db_main)
        forced = ticket_cls._v2_bearer_token()[0]  # noqa: SLF001 — mismo token que emisión v2
        if forced:
            return forced
        setting_data = SettingClass(self.db_main).get()
        return (setting_data.get("setting_data") or {}).get("simplefactura_token")

    def download_pdf(self, dte_id: int):
        dte = self.db2.query(DteModel).filter(DteModel.id == dte_id).first()
        if not dte or not dte.folio:
            return {"status": "error", "message": "DTE no encontrado o sin folio"}

        token = self._simplefactura_bearer_token()
        if not token:
            return {"status": "error", "message": "No hay token SimpleFactura configurado"}

        payload = {
            "credenciales": {
                "rutEmisor": "76063822-6",
                "nombreSucursal": "Casa Matriz",
            },
            "dteReferenciadoExterno": {
                "folio": int(dte.folio),
                "codigoTipoDte": int(dte.dte_type_id or 39),
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

        if response.status_code != 200 or not response.content:
            return {
                "status": "error",
                "message": f"SimpleFactura getPdf HTTP {response.status_code}",
                "detail": (response.text or "")[:300],
            }

        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_filename = f"boleta_caja_{dte.folio}_{timestamp}_{uuid.uuid4().hex[:8]}.pdf"
        remote_path = unique_filename

        self.file_class.temporal_upload(response.content, remote_path)
        file_contents = self.file_class.download(remote_path)
        encoded_file = base64.b64encode(file_contents).decode("utf-8")
        self.file_class.delete(remote_path)

        return {
            "status": "success",
            "file_name": unique_filename,
            "file_data": encoded_file,
        }
