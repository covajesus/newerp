from sqlalchemy.orm import Session
from app.backend.db.models import DteModel, CustomerModel, BranchOfficeModel, ExpenseTypeModel, CustomerDteItemModel
from app.backend.classes.customer_class import CustomerClass
from app.backend.classes.whatsapp_class import WhatsappClass
from app.backend.classes.helper_class import HelperClass, dte_rut_sql_or
from app.backend.classes.file_class import FileClass
from sqlalchemy import desc
from sqlalchemy.dialects import mysql
from sqlalchemy import or_
from datetime import datetime, timedelta
from fastapi import HTTPException
import requests
import json
import base64
import uuid
import os
import time
from sqlalchemy.sql import func
from app.backend.classes.libredte_dte_lines import libredte_detail_line_from_group_item
from app.backend.classes.folio_class import FolioClass
from app.backend.classes.setting_class import SettingClass
from app.backend.classes.dte_pxq_amounts import dte_totals_from_net, pxq_net_total_from_items
from sqlalchemy import text, bindparam

JISBACKEND_SETTINGS_TOKEN_URL = os.getenv(
    "JISBACKEND_SETTINGS_TOKEN_URL",
    "https://jisbackend.com/api/settings/get_token",
)

DTE_VERSION_V2 = 1  # Abonados (mismo que LibreDTE); v2 = emisor externo invoiceV2
DTE_VERSION_V2_LEGACY = 3  # Borradores v2 creados antes de alinear a dte_version_id=1
DTE_V2_BRANCH_SUFFIX = " - JIS PARKING SPA"
DTE_V2_HTTP_TIMEOUT = 30
DTE_CHIP_AMOUNT_CLP = 5000
SIMPLEFACTURA_RUT_EMISOR = "76063822-6"
SIMPLEFACTURA_SUCURSAL = "Casa Matriz"
SIMPLEFACTURA_AMBIENTE = 1


def _is_simplefactura_v2_dte(db: Session, dte) -> bool:
    """Ticket issued via invoiceV2 (folio pool or Klap order), not LibreDTE v1."""
    if int(getattr(dte, "dte_type_id", 0) or 0) != 39:
        return False
    dte_id = getattr(dte, "id", None)
    if dte_id:
        row = db.execute(
            text(
                "SELECT 1 FROM folios "
                "WHERE dte_id = :dte_id AND dte_id > 0 AND document_type_id IN (33, 39) "
                "LIMIT 1"
            ),
            {"dte_id": int(dte_id)},
        ).first()
        if row:
            return True
    folio = getattr(dte, "folio", None)
    if folio:
        from app.backend.db.models import DtePaymentDataModel

        if (
            db.query(DtePaymentDataModel.id)
            .filter(DtePaymentDataModel.folio == int(folio))
            .first()
        ):
            return True
    return False


def sync_simplefactura_paid_status_if_applicable(db: Session, dte) -> dict | None:
    """Call SimpleFactura POST /dte/marcar-pagado-pendiente when a v2 ticket reaches status 5."""
    if not dte:
        return None
    if not _is_simplefactura_v2_dte(db, dte):
        return None
    if int(getattr(dte, "status_id", 0) or 0) != 5:
        return None
    if getattr(dte, "reason_id", None):
        return None
    folio = getattr(dte, "folio", None)
    if not folio:
        return None
    try:
        result = CustomerTicketClass(db).mark_simplefactura_paid_status(int(folio), paid=True)
        print(
            f"[simplefactura] mark-paid folio={folio} status={result.get('status')} "
            f"msg={result.get('message')}",
            flush=True,
        )
        return result
    except Exception as exc:
        print(f"[simplefactura] mark-paid folio={folio} error: {exc}", flush=True)
        return {"status": "error", "message": str(exc)}


def v2_invoice_branch_display(branch) -> str:
    if branch is None:
        return ""
    base_name = (getattr(branch, "branch_office", None) or "").strip()
    if not base_name:
        return ""
    if DTE_V2_BRANCH_SUFFIX.upper() in base_name.upper():
        return base_name
    return f"{base_name}{DTE_V2_BRANCH_SUFFIX}"


def v2_dte_api_date(dt=None) -> str:
    """FchEmis/FchVenc en invoiceV2 (yyyy-mm-dd)."""
    if dt is None:
        return datetime.now().strftime("%Y-%m-%d")
    if isinstance(dt, str):
        raw = dt.strip()[:10]
        if len(raw) == 10 and raw[2] == "-":
            d, m, y = raw.split("-")
            return f"{y}-{m}-{d}"
        if len(raw) == 10 and raw[4] == "-":
            return raw
        return datetime.now().strftime("%Y-%m-%d")
    return dt.strftime("%Y-%m-%d")


def ticket_v2_issuer(branch):
    issuer = {
        "RUTEmisor": "76063822-6",
        "RznSocEmisor": "Jisparking SpA",
        "GiroEmisor": "ESTACIONAMIENTO DE VEHÍCULOS Y PARQUÍMETROS, VENTA DE PRODUCTOS  FARMACEUTICOS",
        "DirOrigen": "Matucana 40",
        "CmnaOrigen": "Santiago",
    }
    if branch is not None and getattr(branch, "dte_code", None) is not None:
        issuer["CdgSIISucur"] = branch.dte_code
    return issuer


def _chip_applies(chip_id, category_id) -> bool:
    return int(chip_id or 0) == 1 and int(category_id or 1) != 3


def document_gross_from_parking(parking_gross: int, chip_id, category_id) -> int:
    """Bruto documento = estacionamiento (+ chip si aplica)."""
    parking = int(parking_gross)
    if _chip_applies(chip_id, category_id):
        return parking + DTE_CHIP_AMOUNT_CLP
    return parking


def document_gross_from_form(form_data) -> int:
    """form_data.amount = monto bruto estacionamiento sin chip."""
    cid = getattr(form_data, "category_id", None)
    if cid is None:
        cid = 1
    return document_gross_from_parking(
        int(form_data.amount),
        getattr(form_data, "chip_id", 0),
        cid,
    )


def _ticket_total_from_form(form_data):
    """Total bruto del documento (estacionamiento + chip si aplica)."""
    return document_gross_from_form(form_data)


def ticket_payment_total(dte) -> int:
    """Monto Klap = dte.total (el chip ya está incluido al guardar)."""
    return int(getattr(dte, "total", 0) or 0)


def _set_dte_gross_totals(dte, gross: int) -> None:
    gross = int(gross)
    dte.cash_amount = gross
    dte.total = gross
    dte.subtotal = round(gross / 1.19)
    dte.tax = gross - dte.subtotal


def _apply_ticket_draft_amounts(dte, form_data, pxq_items=None):
    """Persist draft amounts. Boleta grupal (cat 3): neto desde líneas; total/cash_amount con IVA."""
    cid = getattr(form_data, "category_id", None)
    if cid is None:
        cid = getattr(dte, "category_id", None)
    cid = int(cid or 1)
    chip = int(getattr(form_data, "chip_id", 0) or 0)
    if cid == 3:
        chip = 0

    dte.chip_id = chip
    dte.category_id = cid
    dte.discount = 0
    dte.card_amount = 0

    pxq_net = pxq_net_total_from_items(pxq_items)
    if cid == 3 and pxq_net is not None:
        net, tax, gross, cash = dte_totals_from_net(pxq_net)
        dte.subtotal = net
        dte.tax = tax
        dte.total = gross
        dte.cash_amount = cash
        return

    gross = document_gross_from_form(form_data)
    net = round(gross / 1.19)
    tax = gross - net
    dte.subtotal = net
    dte.tax = tax
    dte.total = gross
    dte.cash_amount = gross


def _sync_ticket_dte_amounts_from_form(dte, form_data, pxq_items=None):
    """Al asignar folio (emitir), alinear cash_amount/total/subtotal/IVA con store."""
    _apply_ticket_draft_amounts(dte, form_data, pxq_items=pxq_items)
    cid = getattr(dte, "category_id", None)
    qty = getattr(form_data, "quantity", None)
    if cid == 3:
        if qty is not None:
            dte.quantity = int(qty)
    else:
        dte.quantity = None


class CustomerTicketClass:
    def __init__(self, db: Session):
        self.db = db
        self.file_class = FileClass(db)  # Crear una instancia de FileClass

    def _clean_optional_str(self, item, *keys):
        for k in keys:
            v = getattr(item, k, None)
            if v is None:
                continue
            s = str(v).strip()
            if s:
                return s
        return None

    def _optional_dsc_item_str(self, item):
        v = getattr(item, "dsc_item", None)
        if v is None:
            return None
        s = str(v).strip()
        return s[:500] if s else None

    def _discount_from_item_input(self, item):
        for k in ("discount_amount", "discount"):
            v = getattr(item, k, None)
            if v is None or v == "":
                continue
            try:
                return max(0, int(v))
            except (TypeError, ValueError):
                return 0
        return 0

    def _normalize_group_items(self, items):
        normalized = []
        if not items:
            return normalized

        for idx, item in enumerate(items, start=1):
            quantity = getattr(item, "quantity", None)
            unit_amount = getattr(item, "unit_amount", None)
            amount = getattr(item, "amount", None)
            detail_only = (getattr(item, "description", None) or "").strip()

            try:
                q = int(quantity)
                u = int(unit_amount)
            except (TypeError, ValueError):
                continue

            name = self._clean_optional_str(item, "item_name")
            code = self._clean_optional_str(item, "item_code")
            if q < 1 or u < 0 or (not detail_only and not name and not code):
                continue

            try:
                total = int(amount) if amount is not None else q * u
            except (TypeError, ValueError):
                total = q * u

            if total <= 0:
                total = q * u

            da = self._discount_from_item_input(item)
            stored_description = detail_only if detail_only else "-"
            dsc = self._optional_dsc_item_str(item)
            if dsc is None and detail_only:
                dsc = detail_only

            normalized.append({
                "line_number": idx,
                "quantity": q,
                "unit_amount": u,
                "total_amount": total,
                "description": stored_description,
                "item_code": code,
                "item_name": name,
                "unit_measure": self._clean_optional_str(item, "unit_measure"),
                "discount_amount": da,
                "dsc_item": dsc,
            })

        return normalized

    def _replace_ticket_items(self, dte_id: int, items):
        self.db.query(CustomerDteItemModel).filter(CustomerDteItemModel.dte_id == dte_id).delete(
            synchronize_session=False
        )
        for item in items:
            self.db.add(
                CustomerDteItemModel(
                    dte_id=dte_id,
                    line_number=item["line_number"],
                    quantity=item["quantity"],
                    unit_amount=item["unit_amount"],
                    total_amount=item["total_amount"],
                    description=item["description"],
                    item_code=item.get("item_code"),
                    item_name=item.get("item_name"),
                    unit_measure=item.get("unit_measure"),
                    discount_amount=int(item.get("discount_amount") or 0),
                    dsc_item=item.get("dsc_item"),
                    status_id=1,
                    added_date=datetime.now(),
                    updated_date=datetime.now()
                )
            )

    def _ticket_draft_id_for_items(self, form_data, source_dte):
        """Prioriza el DTE resuelto (source_dte) sobre form_data.id al leer customer_dte_items."""
        if source_dte is not None and getattr(source_dte, "id", None) is not None:
            return int(source_dte.id)
        raw = getattr(form_data, "id", None)
        if raw is None:
            return None
        try:
            i = int(raw)
        except (TypeError, ValueError):
            return None
        return i if i != 0 else None

    def _get_group_items_for_generation(self, form_data, source_dte=None):
        items = self._normalize_group_items(getattr(form_data, "items", []))
        if items:
            return items

        dte_id = self._ticket_draft_id_for_items(form_data, source_dte)
        if dte_id is not None:
            rows = (
                self.db.query(CustomerDteItemModel)
                .filter(CustomerDteItemModel.dte_id == dte_id)
                .order_by(CustomerDteItemModel.line_number.asc(), CustomerDteItemModel.id.asc())
                .all()
            )
            if rows:
                out = []
                for r in rows:
                    try:
                        q = int(r.quantity)
                        u = int(r.unit_amount)
                        ta = int(r.total_amount)
                    except (TypeError, ValueError):
                        continue
                    if q < 1 or u < 0 or ta < 0:
                        continue
                    da = int(getattr(r, "discount_amount", 0) or 0)
                    out.append({
                        "line_number": r.line_number,
                        "quantity": q,
                        "unit_amount": u,
                        "total_amount": ta,
                        "description": (r.description or "").strip() or f"Ítem {r.line_number}",
                        "item_code": (r.item_code or "").strip() or None,
                        "item_name": (r.item_name or "").strip() or None,
                        "unit_measure": (r.unit_measure or "").strip() or None,
                        "discount_amount": da,
                        "dsc_item": (getattr(r, "dsc_item", None) or "").strip() or None,
                    })
                return out

        return []

    def _v2_folio_pool_dte_ids(self, dte_ids):
        """DTE ids whose folio was reserved from the central pool (v2 emit)."""
        ids = [int(i) for i in (dte_ids or []) if i not in (None, "", 0)]
        if not ids:
            return set()
        stmt = text(
            "SELECT DISTINCT dte_id FROM folios "
            "WHERE dte_id IN :dte_ids AND dte_id > 0 "
            "AND document_type_id IN (33, 39)"
        ).bindparams(bindparam("dte_ids", expanding=True))
        rows = self.db.execute(stmt, {"dte_ids": ids}).scalars().all()
        return {int(r) for r in rows if r is not None}

    def get_all(self, rol_id = None, rut = None, group=1, page=0, items_per_page=10, period=None, dte_version_id=1, include_emitted=False):
        try:
            if rol_id == 1 or rol_id == 2:
                # Inicialización de filtros dinámicos
                filters = []

                filters.append(DteModel.dte_version_id == dte_version_id)
                filters.append(DteModel.dte_type_id == 39)
                filters.append(DteModel.rut != None)

                if group == 1:
                    if include_emitted:
                        filters.append(
                            or_(
                                DteModel.status_id == 1,
                                DteModel.status_id == 2,
                                DteModel.status_id == 3,
                                DteModel.status_id == 4,
                            )
                        )
                    else:
                        filters.append(or_(DteModel.status_id == 1, DteModel.status_id == 2, DteModel.status_id == 3))

                    current_period = datetime.now().strftime('%Y-%m')
                    filters.append(DteModel.period == current_period)

                    # Construir la consulta base con los filtros aplicados
                    query = self.db.query(
                        DteModel.id, 
                        DteModel.branch_office_id, 
                        DteModel.folio, 
                        DteModel.total,
                        DteModel.added_date,
                        DteModel.rut,
                        DteModel.status_id,
                        DteModel.chip_id,
                        DteModel.category_id,
                        CustomerModel.customer,
                        BranchOfficeModel.branch_office
                    ).outerjoin(
                        BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
                    ).outerjoin(
                        CustomerModel, CustomerModel.rut == DteModel.rut
                    ).filter(
                        *filters
                    ).order_by(
                        desc(DteModel.status_id)
                    )
                else:
                    filters.append(or_(DteModel.status_id == 4, DteModel.status_id == 5))
            
                    # Construir la consulta base con los filtros aplicados
                    query = self.db.query(
                        DteModel.id, 
                        DteModel.branch_office_id, 
                        DteModel.folio, 
                        DteModel.total,
                        DteModel.added_date,
                        DteModel.rut,
                        DteModel.status_id,
                        DteModel.chip_id,
                        DteModel.category_id,
                        CustomerModel.customer,
                        BranchOfficeModel.branch_office
                    ).outerjoin(
                        BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
                    ).outerjoin(
                        CustomerModel, CustomerModel.rut == DteModel.rut
                    ).filter(
                        *filters
                    ).order_by(
                        desc(DteModel.folio)
                    )
            elif rol_id == 4:
                # Inicialización de filtros dinámicos
                filters = []

                filters.append(DteModel.dte_version_id == dte_version_id)
                filters.append(DteModel.dte_type_id == 39)
                filters.append(DteModel.rut != None)

                if group == 1:
                    if include_emitted:
                        filters.append(
                            or_(
                                DteModel.status_id == 1,
                                DteModel.status_id == 2,
                                DteModel.status_id == 3,
                                DteModel.status_id == 4,
                            )
                        )
                    else:
                        filters.append(or_(DteModel.status_id == 1, DteModel.status_id == 2, DteModel.status_id == 3))

                    current_period = datetime.now().strftime('%Y-%m')
                    filters.append(DteModel.period == current_period)

                    # Construir la consulta base con los filtros aplicados
                    query = self.db.query(
                        DteModel.id, 
                        DteModel.branch_office_id, 
                        DteModel.folio, 
                        DteModel.total,
                        DteModel.added_date,
                        DteModel.rut,
                        DteModel.status_id,
                        DteModel.chip_id,
                        DteModel.category_id,
                        CustomerModel.customer,
                        BranchOfficeModel.branch_office
                    ).outerjoin(
                        BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
                    ).outerjoin(
                        CustomerModel, CustomerModel.rut == DteModel.rut
                    ).filter(
                        BranchOfficeModel.principal_supervisor == rut
                    ).filter(
                        *filters
                    ).order_by(
                        desc(DteModel.status_id)
                    )
                else:
                    filters.append(or_(DteModel.status_id == 4, DteModel.status_id == 5))
            
                    # Construir la consulta base con los filtros aplicados
                    query = self.db.query(
                        DteModel.id, 
                        DteModel.branch_office_id, 
                        DteModel.folio, 
                        DteModel.total,
                        DteModel.added_date,
                        DteModel.rut,
                        DteModel.status_id,
                        DteModel.chip_id,
                        DteModel.category_id,
                        CustomerModel.customer,
                        BranchOfficeModel.branch_office
                    ).outerjoin(
                        BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
                    ).outerjoin(
                        CustomerModel, CustomerModel.rut == DteModel.rut
                    ).filter(
                        BranchOfficeModel.principal_supervisor == rut
                    ).filter(
                        *filters
                    ).order_by(
                        desc(DteModel.folio)
                    )

            # Si se solicita paginación
            if page > 0:
                # Calcular el total de registros
                total_items = query.count()
                print(query.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))

                total_pages = (total_items + items_per_page - 1) // items_per_page
                print(total_pages)
                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                # Aplicar paginación en la consulta
                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                v2_folio_pool_ids = self._v2_folio_pool_dte_ids([d.id for d in data])

                # Serializar los datos
                serialized_data = [{
                    "id": dte.id,
                    "rut": dte.rut,
                    "branch_office_id": dte.branch_office_id,
                    "customer": dte.customer,
                    "chip_id": dte.chip_id,
                    "category_id": dte.category_id if dte.category_id is not None else 1,
                    "folio": dte.folio,
                    "total": dte.total,
                    "status_id": dte.status_id,
                    "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                    "branch_office": dte.branch_office,
                    "v2_emit": dte.id in v2_folio_pool_ids,
                } for dte in data]

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }

            # Si no se solicita paginación, traer todos los datos
            else:
                data = query.all()

                v2_folio_pool_ids = self._v2_folio_pool_dte_ids([d.id for d in data])

                # Serializar los datos
                serialized_data = [{
                    "id": dte.id,
                    "rut": dte.rut,
                    "branch_office_id": dte.branch_office_id,
                    "customer": dte.customer,
                    "chip_id": dte.chip_id,
                    "category_id": dte.category_id if dte.category_id is not None else 1,
                    "folio": dte.folio,
                    "total": dte.total,
                    "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                    "branch_office": dte.branch_office,
                    "status_id": dte.status_id,
                    "v2_emit": dte.id in v2_folio_pool_ids,
                } for dte in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}

    def search(self, rol_id = None, supervisor_rut = None, branch_office_id=None, rut=None, customer=None, status_id=None, supervisor_id=None, page=0, items_per_page=10, category_id=None, dte_version_id=1, include_emitted=False):
        try:
            if rol_id == 1 or rol_id == 2:
                # Filtros: borradores boleta (39), período mes actual. 0 en sucursal = todas.
                filters = []

                if branch_office_id is not None and branch_office_id != "" and branch_office_id != 0:
                    filters.append(DteModel.branch_office_id == branch_office_id)
                if rut is not None and str(rut).strip() != "":
                    filters.append(dte_rut_sql_or(DteModel.rut, rut))
                if customer is not None and customer != "":
                    filters.append(CustomerModel.customer.like(f"%{customer}%"))
                # Evitar mezclar status_id explícito con status_id < 4 a la vez (contradicciones).
                if status_id is not None and status_id != "":
                    filters.append(DteModel.status_id == status_id)
                elif include_emitted:
                    filters.append(DteModel.status_id.in_((1, 2, 3, 4)))
                else:
                    filters.append(DteModel.status_id < 4)

                filters.append(DteModel.dte_version_id == dte_version_id)
                filters.append(DteModel.dte_type_id == 39)
                filters.append(DteModel.rut != None)
                filters.append(DteModel.period == datetime.now().strftime('%Y-%m'))

                if supervisor_id is not None and supervisor_id != "":
                    filters.append(BranchOfficeModel.principal_supervisor == supervisor_id)
                if category_id is not None and category_id != "" and category_id != 0:
                    filters.append(DteModel.category_id == category_id)

                query = self.db.query(
                    DteModel.id,
                    DteModel.branch_office_id,
                    DteModel.folio,
                    DteModel.total,
                    DteModel.added_date,
                    DteModel.rut,
                    DteModel.status_id,
                    DteModel.chip_id,
                    DteModel.category_id,
                    CustomerModel.customer,
                    BranchOfficeModel.branch_office
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
                ).outerjoin(
                    CustomerModel, CustomerModel.rut == DteModel.rut
                ).filter(
                    *filters
                ).order_by(
                    DteModel.folio.desc()
                )

                # Si se solicita paginación
                if page > 0:
                    # Calcular el total de registros
                    total_items = query.count()
                    print(query.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))

                    total_pages = (total_items + items_per_page - 1) // items_per_page
                    print(total_pages)
                    if page < 1 or page > total_pages:
                        return {"status": "error", "message": "Invalid page number"}

                    # Aplicar paginación en la consulta
                    data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                    if not data:
                        return {"status": "error", "message": "No data found"}

                    # Serializar los datos
                    serialized_data = [{
                        "id": dte.id,
                        "rut": dte.rut,
                        "branch_office_id": dte.branch_office_id,
                        "customer": dte.customer,
                        "chip_id": dte.chip_id,
                        "category_id": dte.category_id if dte.category_id is not None else 1,
                        "folio": dte.folio,
                        "total": dte.total,
                        "status_id": dte.status_id,
                        "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                        "branch_office": dte.branch_office
                    } for dte in data]

                    return {
                        "total_items": total_items,
                        "total_pages": total_pages,
                        "current_page": page,
                        "items_per_page": items_per_page,
                        "data": serialized_data
                    }

                # Si no se solicita paginación, traer todos los datos
                else:
                    data = query.all()

                    # Serializar los datos
                    serialized_data = [{
                        "id": dte.id,
                        "rut": dte.rut,
                        "branch_office_id": dte.branch_office_id,
                        "customer": dte.customer,
                        "folio": dte.folio,
                        "chip_id": dte.chip_id,
                        "category_id": dte.category_id if dte.category_id is not None else 1,
                        "total": dte.total,
                        "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                        "branch_office": dte.branch_office,
                        "status_id": dte.status_id
                    } for dte in data]

                    return {
                        "data": serialized_data
                    }
            elif rol_id == 4:
                filters = []

                if branch_office_id is not None and branch_office_id != "" and branch_office_id != 0:
                    filters.append(DteModel.branch_office_id == branch_office_id)
                if rut is not None and str(rut).strip() != "":
                    filters.append(dte_rut_sql_or(DteModel.rut, rut))
                if customer is not None and customer != "":
                    filters.append(CustomerModel.customer.like(f"%{customer}%"))
                if status_id is not None and status_id != "":
                    filters.append(DteModel.status_id == status_id)
                elif include_emitted:
                    filters.append(DteModel.status_id.in_((1, 2, 3, 4)))
                else:
                    filters.append(DteModel.status_id < 4)
                if category_id is not None and category_id != "" and category_id != 0:
                    filters.append(DteModel.category_id == category_id)

                filters.append(DteModel.dte_version_id == dte_version_id)
                filters.append(DteModel.dte_type_id == 39)
                filters.append(DteModel.rut != None)
                filters.append(DteModel.period == datetime.now().strftime('%Y-%m'))

                query = self.db.query(
                    DteModel.id,
                    DteModel.branch_office_id,
                    DteModel.folio,
                    DteModel.total,
                    DteModel.added_date,
                    DteModel.rut,
                    DteModel.status_id,
                    DteModel.chip_id,
                    DteModel.category_id,
                    CustomerModel.customer,
                    BranchOfficeModel.branch_office
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
                ).outerjoin(
                    CustomerModel, CustomerModel.rut == DteModel.rut
                ).filter(
                    BranchOfficeModel.principal_supervisor == supervisor_rut
                ).filter(
                    *filters
                ).order_by(
                    DteModel.folio.desc()
                )

                # Si se solicita paginación
                if page > 0:
                    # Calcular el total de registros
                    total_items = query.count()
                    print(query.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))

                    total_pages = (total_items + items_per_page - 1) // items_per_page
                    print(total_pages)
                    if page < 1 or page > total_pages:
                        return {"status": "error", "message": "Invalid page number"}

                    # Aplicar paginación en la consulta
                    data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                    if not data:
                        return {"status": "error", "message": "No data found"}

                    # Serializar los datos
                    serialized_data = [{
                        "id": dte.id,
                        "rut": dte.rut,
                        "branch_office_id": dte.branch_office_id,
                        "customer": dte.customer,
                        "chip_id": dte.chip_id,
                        "category_id": dte.category_id if dte.category_id is not None else 1,
                        "folio": dte.folio,
                        "total": dte.total,
                        "status_id": dte.status_id,
                        "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                        "branch_office": dte.branch_office
                    } for dte in data]

                    return {
                        "total_items": total_items,
                        "total_pages": total_pages,
                        "current_page": page,
                        "items_per_page": items_per_page,
                        "data": serialized_data
                    }

                # Si no se solicita paginación, traer todos los datos
                else:
                    data = query.all()

                    # Serializar los datos
                    serialized_data = [{
                        "id": dte.id,
                        "rut": dte.rut,
                        "branch_office_id": dte.branch_office_id,
                        "customer": dte.customer,
                        "folio": dte.folio,
                        "chip_id": dte.chip_id,
                        "category_id": dte.category_id if dte.category_id is not None else 1,
                        "total": dte.total,
                        "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                        "branch_office": dte.branch_office,
                        "status_id": dte.status_id
                    } for dte in data]

                    return {
                        "data": serialized_data
                    }
        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
    
    def update(self, form_data):
        dte = self.db.query(DteModel).filter(DteModel.id == form_data.id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        dte.branch_office_id = form_data.branch_office_id
        dte.rut = form_data.rut
        dte.chip_id = form_data.chip_id
        dte.status_id = 2

        cid = getattr(form_data, "category_id", None)
        effective_cid = int(cid) if cid is not None else int(dte.category_id or 1)
        if cid is not None:
            dte.category_id = effective_cid

        group_items = self._normalize_group_items(getattr(form_data, "items", []))
        qty = getattr(form_data, "quantity", None)
        if effective_cid == 3:
            if group_items:
                dte.quantity = sum(item["quantity"] for item in group_items)
                self._replace_ticket_items(dte.id, group_items)
            elif qty is not None:
                dte.quantity = int(qty)
        elif cid is not None:
            dte.category_id = 1
            dte.quantity = None
            self.db.query(CustomerDteItemModel).filter(CustomerDteItemModel.dte_id == dte.id).delete(
                synchronize_session=False
            )

        _apply_ticket_draft_amounts(dte, form_data, pxq_items=group_items if group_items else None)

        self.db.commit()
        self.db.refresh(dte)
    
    def change_status(self, form_data):
        dte = self.db.query(DteModel).filter(DteModel.id == form_data.id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        dte.expense_type_id = form_data.expense_type_id
        dte.payment_type_id = form_data.payment_type_id
        dte.payment_date = form_data.payment_date
        period = form_data.payment_date.split('-')
        dte.period = period[0] + '-' + period[1]
        dte.comment = form_data.comment
        dte.status_id = 5

        self.db.commit()
        self.db.refresh(dte)

        self.create_account_asset(dte)
        sync_simplefactura_paid_status_if_applicable(self.db, dte)

    def reject(self, id):
        dte = self.db.query(DteModel).filter(DteModel.id == id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        dte.status_id = 3

        self.db.commit()
        self.db.refresh(dte)

    def get(self, id):
        try:
            data_query = self.db.query(
                DteModel.id,
                DteModel.rut,
                DteModel.branch_office_id,
                DteModel.total,
                CustomerModel.address,
                DteModel.cash_amount,
                CustomerModel.customer,
                CustomerModel.region_id,
                CustomerModel.commune_id,
                CustomerModel.activity,
                CustomerModel.email,
                CustomerModel.phone,
                DteModel.chip_id,
                DteModel.folio,
                DteModel.status_id,
                DteModel.added_date,
                BranchOfficeModel.branch_office,
                DteModel.category_id,
            ).outerjoin(BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id).outerjoin(
                CustomerModel, CustomerModel.rut == DteModel.rut
            ).filter(DteModel.id == id).first()

            if data_query:
                item_rows = (
                    self.db.query(CustomerDteItemModel)
                    .filter(CustomerDteItemModel.dte_id == id)
                    .order_by(CustomerDteItemModel.line_number.asc(), CustomerDteItemModel.id.asc())
                    .all()
                )
                items_payload = [
                    {
                        "line_number": r.line_number,
                        "quantity": int(r.quantity),
                        "unit_amount": int(r.unit_amount),
                        "total_amount": int(r.total_amount),
                        "description": (r.description or "").strip(),
                        "item_code": (r.item_code or "").strip() or None,
                        "item_name": (r.item_name or "").strip() or None,
                        "unit_measure": (r.unit_measure or "").strip() or None,
                        "discount_amount": int(getattr(r, "discount_amount", 0) or 0),
                        "dsc_item": (getattr(r, "dsc_item", None) or "").strip() or None,
                    }
                    for r in item_rows
                ]

                customer_ticket_data = {
                    "id": data_query.id,
                    "rut": data_query.rut,
                    "branch_office_id": data_query.branch_office_id,
                    "customer": data_query.customer,
                    "email": data_query.email,
                    "phone": data_query.phone,
                    "chip_id": data_query.chip_id,
                    "folio": data_query.folio,
                    "activity": data_query.activity,
                    "region_id": data_query.region_id,
                    "commune_id": data_query.commune_id,
                    "address": data_query.address,
                    "total": data_query.total,
                    "status_id": data_query.status_id,
                    "added_date": data_query.added_date.strftime('%d-%m-%Y') if data_query.added_date else None,
                    "branch_office": data_query.branch_office,
                    "category_id": data_query.category_id,
                    "items": items_payload,
                }

                result = {
                    "customer_ticket_data": customer_ticket_data
                }

                serialized_result = json.dumps(result)

                return serialized_result

            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def save_pdf_ticket(self, folio):
        folio = folio
        tipo_dte = 39
        rut_emisor = '76063822'
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        # URL completa
        url = f"https://libredte.cl/api/dte/dte_emitidos/pdf/{tipo_dte}/{folio}/{rut_emisor}?formato=general&papelContinuo=0&copias_tributarias=1&copias_cedibles=1&cedible=0&compress=0&base64=0"

        # Headers con token de autenticación
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {TOKEN}'
        }

        # Realizar la solicitud
        response = requests.get(url, headers=headers)

        # Verificar respuesta
        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
        else:
            # Guardar el PDF en disco
            with open(f'files/{folio}.pdf', 'wb') as f:
                f.write(response.content)
            print(f'PDF guardado como {folio}.pdf')

    def _expected_total_for_generate(self, form_data) -> int:
        """Total bruto para ubicar el borrador (misma regla que store; cat. 3 no es especial salvo ítems)."""
        return _ticket_total_from_form(form_data)

    def _ticket_source_dte_from_form(self, form_data):
        dte_id = getattr(form_data, "id", None)
        try:
            did_int = int(dte_id) if dte_id not in (None, "", False) else None
        except (TypeError, ValueError):
            did_int = None
        if did_int:
            return self.db.query(DteModel).filter(DteModel.id == did_int).first()
        return None

    def _ticket_pre_detalle_lines_from_form(self, form_data, source_dte=None, *, libredte_v1: bool = False):
        """
        Líneas Detalle para boleta 39.
        libredte_v1=True: boleta grupal PXQ envía PrcItem bruto (LibreDTE v1 emitir).
        """
        category_id = getattr(form_data, "category_id", None)
        if category_id is None and source_dte is not None:
            category_id = source_dte.category_id
        if category_id is None:
            category_id = 1
        if category_id not in (1, 3):
            category_id = 1

        qty = getattr(form_data, "quantity", None)
        if qty is None and source_dte is not None and source_dte.quantity is not None:
            qty = source_dte.quantity
        try:
            qty = int(qty) if qty not in (None, "", 0) else None
        except (TypeError, ValueError):
            qty = None

        group_items = self._get_group_items_for_generation(form_data, source_dte)

        if category_id == 3:
            if not group_items:
                return {
                    "status": "error",
                    "message": (
                        "Boleta grupal (categoría 3) sin líneas de ítem: cargue ítems en la petición o guarde líneas "
                        "en customer_dte_items para el borrador."
                    ),
                }
            detail_lines = []
            for item in group_items:
                detail_lines.append(
                    libredte_detail_line_from_group_item(
                        item,
                        include_line_amount=False,
                        unit_prices_gross=libredte_v1,
                    )
                )
            if form_data.chip_id == 1:
                detail_lines.append(
                    {
                        "NmbItem": "Chip",
                        "QtyItem": 1,
                        "PrcItem": DTE_CHIP_AMOUNT_CLP,
                    }
                )
            return detail_lines

        if form_data.chip_id == 1:
            parking = int(form_data.amount)
            return [
                {
                    "NmbItem": " Prestación de estacionamientos. Fecha:"
                    + datetime.now().strftime("%d-%m-%Y"),
                    "QtyItem": 1,
                    "PrcItem": parking,
                },
                {
                    "NmbItem": "Chip",
                    "QtyItem": 1,
                    "PrcItem": DTE_CHIP_AMOUNT_CLP,
                },
            ]

        if qty is not None and qty >= 1:
            q = qty
            unit_price = round(int(form_data.amount) / q) if q > 0 else int(form_data.amount)
            return [
                {
                    "NmbItem": " Prestación de estacionamientos. Fecha:"
                    + datetime.now().strftime("%d-%m-%Y"),
                    "QtyItem": q,
                    "PrcItem": unit_price,
                }
            ]

        amt = int(form_data.amount)
        return [
            {
                "NmbItem": " Prestación de estacionamientos. Fecha:"
                + datetime.now().strftime("%d-%m-%Y"),
                "QtyItem": 1,
                "PrcItem": amt,
            }
        ]

    def _v2_format_detalle_lines(self, detail_lines, category_id: int) -> tuple[list, int]:
        """
        Detalle invoiceV2 (gateway v2).
        Cat. 1: PrcItem en líneas pre-generadas es bruto (como LibreDTE).
        Cat. 3 (group): PrcItem es neto (BD); Totales v2 con IndMntNeto=2.
        """
        prices_are_net = int(category_id or 1) == 3
        formatted_lines: list[dict] = []
        total_gross = 0
        for index, line in enumerate(detail_lines, start=1):
            qty = int(line.get("QtyItem", 1) or 1)
            prc_raw = int(line.get("PrcItem", 0) or 0)
            monto_raw = line.get("MontoItem")
            if prices_are_net:
                line_net = int(monto_raw) if monto_raw is not None else qty * prc_raw
                unit_net = prc_raw if qty <= 1 else max(0, round(line_net / qty))
                line_gross = round(line_net * 1.19)
            else:
                line_gross = int(monto_raw) if monto_raw is not None else qty * prc_raw
                line_net = round(line_gross / 1.19)
                unit_net = round(prc_raw / 1.19) if prc_raw else 0
            total_gross += line_gross
            entry = {
                "NroLinDet": str(index),
                "NmbItem": line.get("NmbItem", "Item"),
                "QtyItem": str(qty),
                "UnmdItem": line.get("UnmdItem") or "un",
                "PrcItem": unit_net,
                "MontoItem": line_net,
            }
            if line.get("DscItem"):
                entry["DscItem"] = line["DscItem"]
            if line.get("CdgItem"):
                entry["CdgItem"] = line["CdgItem"]
            formatted_lines.append(entry)
        return formatted_lines, total_gross

    def _ticket_receiver_from_customer(self, customer_data: dict) -> dict:
        cd = customer_data["customer_data"]
        return {
            "RUTRecep": cd["rut"],
            "RznSocRecep": cd["customer"],
            "GiroRecep": cd.get("activity"),
            "DirRecep": cd.get("region"),
            "CmnaRecep": cd.get("commune"),
            "Contacto": cd.get("email"),
            "CorreoRecep": cd.get("email"),
        }

    def generate(self, form_data):
        expected_total_doc = self._expected_total_for_generate(form_data)
        check_dte_existence = self.db.query(DteModel).filter(
            DteModel.branch_office_id == form_data.branch_office_id,
            DteModel.rut == form_data.rut,
            DteModel.total == expected_total_doc,
            DteModel.dte_type_id == 39,
            DteModel.dte_version_id == 1,
            DteModel.status_id == 4,
            DteModel.period == datetime.now().strftime('%Y-%m')
        ).count()

        if check_dte_existence == 0:
            customer = CustomerClass(self.db).get_by_rut(form_data.rut)
            customer_data = json.loads(customer)

            code = self.pre_generate_ticket(customer_data, form_data)
            folio = None
            generar_err = None

            if isinstance(code, dict) and code.get("status") == "error":
                return code

            if code is None:
                return {
                    "status": "error",
                    "message": "LibreDTE (emitir) no devolvió código de autorización.",
                }

            if code == 402:
                return "LibreDTE payment required"

            if isinstance(code, int):
                return {
                    "status": "error",
                    "message": (
                        f"Respuesta inválida en paso emitir ({code}). Revise XML/payload o token LibreDTE."
                    ),
                }

            folio, generar_err = self.generate_ticket(customer_data["customer_data"]["rut"], code)

            if folio is not None:
                self.save_pdf_ticket(folio)

            # store() usa status_id=2 (admin/supervisor) o 1 (rol cajero). Borrador folio=0.
            # 1) Match estricto con total; 2) mismo RUT/sucursal/periodo sin total (chip/monto redondeo).
            if folio is not None:
                period_str = datetime.now().strftime("%Y-%m")
                expected_total = expected_total_doc
                rut_clause = dte_rut_sql_or(DteModel.rut, form_data.rut)

                def _find_draft(require_total: bool):
                    q = (
                        self.db.query(DteModel)
                        .filter(
                            DteModel.branch_office_id == form_data.branch_office_id,
                            rut_clause,
                            DteModel.dte_type_id == 39,
                            DteModel.dte_version_id == 1,
                            DteModel.status_id.in_((1, 2)),
                            DteModel.period == period_str,
                            DteModel.folio == 0,
                        )
                    )
                    if require_total:
                        q = q.filter(DteModel.total == expected_total)
                    return q.order_by(DteModel.id.desc()).first()

                dte = _find_draft(True)
                if dte is None:
                    dte = _find_draft(False)
                if dte is None:
                    dte = (
                        self.db.query(DteModel)
                        .filter(
                            DteModel.branch_office_id == form_data.branch_office_id,
                            rut_clause,
                            DteModel.dte_type_id == 39,
                            DteModel.dte_version_id == 1,
                            DteModel.status_id.in_((1, 2)),
                            DteModel.period == period_str,
                        )
                        .order_by(DteModel.id.desc())
                        .first()
                    )

                if dte:
                    dte.folio = folio
                    dte.status_id = 4
                    group_items = self._get_group_items_for_generation(form_data, dte)
                    _sync_ticket_dte_amounts_from_form(
                        dte, form_data, pxq_items=group_items if group_items else None
                    )
                    if getattr(dte, "category_id", None) == 3:
                        if group_items:
                            dte.quantity = sum(item["quantity"] for item in group_items)
                            if self._normalize_group_items(getattr(form_data, "items", [])):
                                self._replace_ticket_items(dte.id, group_items)
                        elif getattr(form_data, "quantity", None) is not None:
                            dte.quantity = int(form_data.quantity)

                    try:
                        self.db.commit()
                        self.db.refresh(dte)

                        print("Empieza envio de whatsapp")

                        WhatsappClass(self.db).send(dte, form_data.rut)

                        return {"status": "success", "message": "Dte saved successfully"}
                    except Exception as e:
                        self.db.rollback()
                        return {"status": "error", "message": f"Error: {str(e)}"}
                else:
                    return {
                        "status": "error",
                        "message": "Dte not found after generation (no hay borrador tipo 39 para este RUT/monto/sucursal o el total no coincide).",
                    }
            else:
                msg = generar_err or "LibreDTE (generar) no devolvió folio."
                return {"status": "error", "message": msg}
        else:
            return {"status": "error", "message": "Dte already exists for this RUT in the current period"}
        
    def store(self, form_data, rol_id):
        if form_data.will_save == 1:
            dte = DteModel()

            period = datetime.now().strftime('%Y-%m')

            if rol_id == 1 or rol_id == 2:
                status_id = 2
            elif rol_id == 4:
                status_id = 1
                    
            # Asignar los valores del formulario a la instancia del modelo
            dte.branch_office_id = form_data.branch_office_id
            dte.cashier_id = 0
            dte.dte_type_id = 39
            dte.dte_version_id = 1
            dte.status_id = status_id
            dte.chip_id = form_data.chip_id
            dte.rut = form_data.rut
            dte.folio = 0
            cid = getattr(form_data, "category_id", None)
            dte.category_id = cid if cid is not None else 1

            group_items = self._normalize_group_items(getattr(form_data, "items", []))
            _apply_ticket_draft_amounts(dte, form_data, pxq_items=group_items if group_items else None)
            qty = getattr(form_data, "quantity", None)
            if dte.category_id == 3 and group_items:
                dte.quantity = sum(item["quantity"] for item in group_items)
            elif dte.category_id == 3 and qty is not None:
                dte.quantity = int(qty)
            else:
                dte.quantity = None

            dte.period = period
            dte.added_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            self.db.add(dte)

            try:
                self.db.flush()
                if dte.category_id == 3 and group_items:
                    self._replace_ticket_items(dte.id, group_items)
                self.db.commit()

                return {"status": "success", "message": "Dte saved successfully"}
            except Exception as e:
                self.db.rollback()
                return {"status": "error", "message": f"Error: {str(e)}"}
        else:
            return 'error'
            
    def create_account_asset(self, form_data):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        if form_data.dte_type_id == 39:
            american_date = form_data.period + '-01'
            utf8_date = HelperClass.convert_to_utf8(american_date)
            expense_type = self.db.query(ExpenseTypeModel).filter(
                ExpenseTypeModel.id == form_data.expense_type_id
            ).first()
            branch_office = self.db.query(BranchOfficeModel).filter(
                BranchOfficeModel.id == form_data.branch_office_id
            ).first()

            gloss = (
                branch_office.branch_office
                + "_"
                + expense_type.accounting_account
                + "_"
                + utf8_date
                + "_BoletaElectronica_"
                + str(form_data.id)
                + "_"
                + str(form_data.folio)
            )
            amount = form_data.total
        
            data = {
                "fecha": american_date,
                "glosa": gloss,
                "detalle": {
                    "debe": {
                        "111000102": amount,
                    },
                    "haber": {
                        expense_type.accounting_account.strip(): round(amount / 1.19),
                        "221000226": round(amount - (amount / 1.19)),
                    }
                },
                "operacion": "I",
                "documentos": {
                    "emitidos": [
                        {
                            "dte": form_data.dte_type_id,
                            "folio": form_data.folio,
                        }
                    ]
                },
            }
        else:
            american_date = form_data.period + '-01'
            utf8_date = HelperClass.convert_to_utf8(american_date)
            expense_type = self.db.query(ExpenseTypeModel).filter(
                ExpenseTypeModel.id == form_data.expense_type_id
            ).first()
            branch_office = self.db.query(BranchOfficeModel).filter(
                BranchOfficeModel.id == form_data.branch_office_id
            ).first()

            gloss = (
                branch_office.branch_office
                + "_"
                + expense_type.accounting_account
                + "_"
                + utf8_date
                + "_NotaCredito_"
                + str(form_data.id)
                + "_"
                + str(form_data.folio)
            )
            amount = form_data.total
        
            data = {
                "fecha": american_date,
                "glosa": gloss,
                "detalle": {
                    "debe": {
                        expense_type.accounting_account.strip(): round(amount / 1.19),
                        "221000226": round(amount - (amount / 1.19)),
                    },
                    "haber": {
                        "111000102": amount,
                    }
                },
                "operacion": "I",
                "documentos": {
                    "emitidos": [
                        {
                            "dte": form_data.dte_type_id,
                            "folio": form_data.folio,
                        }
                    ]
                },
            }

        try:
            url = f"https://libredte.cl/api/lce/lce_asientos/crear/" + "76063822"

            response = requests.post(
                url,
                json=data,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 200:
                return "Accounting entry created successfully"
            else:
                return f"Accounting entry creation failed."

        except Exception as e:
            print("Error al conectarse a la API:", e)
            return None
    
    def store_credit_note(self, form_data):
        dte = self.db.query(DteModel).filter(DteModel.id == form_data.id).first()
        
        customer = CustomerClass(self.db).get_by_rut(dte.rut)
        customer_data = json.loads(customer)

        dte_date = self.get_dte_date(dte.folio)

        code = self.pre_generate_credit_note_ticket(customer_data, dte.folio, dte.cash_amount, dte_date)

        folio = None

        if code is not None:
            if code == 402:
                return "LibreDTE payment required"

            folio = self.generate_credit_note_ticket(customer_data['customer_data']['rut'], code)

        if folio != None:
            dte.status_id = 5
            dte.reason_id = form_data.reason_id
            dte.comment = 'Código de autorización: Nota de Crédito ' + str(code)
            self.db.add(dte)
            self.db.commit()

            credit_note_dte = DteModel()
                    
            # Asignar los valores del formulario a la instancia del modelo
            credit_note_dte.branch_office_id = dte.branch_office_id
            credit_note_dte.cashier_id = dte.cashier_id
            credit_note_dte.dte_type_id = 61
            credit_note_dte.dte_version_id = 1
            credit_note_dte.status_id = 5
            credit_note_dte.chip_id = 0
            credit_note_dte.rut = customer_data['customer_data']['rut']
            credit_note_dte.folio = folio
            credit_note_dte.cash_amount = dte.cash_amount
            credit_note_dte.card_amount = 0
            credit_note_dte.subtotal = round(dte.cash_amount/1.19)
            credit_note_dte.tax = (dte.cash_amount) - round((dte.cash_amount)/1.19)
            credit_note_dte.discount = 0
            credit_note_dte.total = dte.cash_amount
            credit_note_dte.added_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            credit_note_dte.category_id = 1
            credit_note_dte.quantity = None

            self.db.add(credit_note_dte)
            
            try:
                self.db.commit()

                return {"status": "success", "message": "Credit Note saved successfully"}
            except Exception as e:
                self.db.rollback()
                return {"status": "error", "message": f"Error: {str(e)}"}
        else:
            return "Creditnote was not created"
        
    def pre_generate_ticket(self, customer_data, form_data):  # Added self as the first argument
        branch_office_data = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == form_data.branch_office_id).first()

        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        source_dte = self._ticket_source_dte_from_form(form_data)
        detail_lines = self._ticket_pre_detalle_lines_from_form(form_data, source_dte, libredte_v1=True)
        if isinstance(detail_lines, dict) and detail_lines.get("status") == "error":
            return detail_lines

        er = {
            "Emisor": {
                "RUTEmisor": "76063822-6",
                "CdgSIISucur": branch_office_data.dte_code,
            },
            "Receptor": self._ticket_receiver_from_customer(customer_data),
        }

        data = {
            "Encabezado": {
                "IdDoc": {"TipoDTE": 39},
                **er,
            },
            "Detalle": detail_lines,
        }

        # Boleta grupal: Totales van dentro de Encabezado (ver `pre_generate_credit_note_ticket` en
        # customer_ticket_bill_class). Un nodo "Totales" en la raíz del documento invalida el XML (error TED).
        try:
            # normalizar=1: LibreDTE completa IdDoc/FchEmis y cuadra detalle (normalizar=0 suele dar HTTP 400 si falta algo).
            url = f"https://libredte.cl/api/dte/documentos/emitir?normalizar=1&formato=json&links=0&email=0"
            
            # Enviar solicitud a la API
            response = requests.post(
                url,
                json=data,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )
            
            # Manejar la respuesta
            if response.status_code == 200:
                dte_data = response.json()
                code = dte_data.get("codigo")

                return code
            else:
                detail = (response.text or "")[:2500]
                try:
                    err_j = response.json()
                    if isinstance(err_j, dict):
                        detail = (
                            err_j.get("mensaje")
                            or err_j.get("detalle")
                            or err_j.get("error")
                            or err_j.get("glosa")
                            or detail
                            or str(err_j)
                        )
                except Exception:
                    pass
                return {
                    "status": "error",
                    "message": f"LibreDTE emitir HTTP {response.status_code}: {detail}",
                }

        except Exception as e:
            print("Error al conectarse a la API:", e)
            return None
    
    def get_dte_date(self, folio):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        # Endpoint para generar un DTE temporal
        url = f"https://libredte.cl/api/dte/dte_emitidos/info/39/" + str(folio) + '/76063822?getXML=0&getDetalle=0&getDatosDte=0&getTed=0&getResolucion=0&getEmailEnviados=0&getLinks=0&getReceptor=0&getSucursal=0&getUsuario=0'
            
        # Enviar solicitud a la API
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
            },
        )

        response_data = response.json()

        return response_data['fecha']

    def pre_generate_credit_note_ticket(self, customer_data, folio, cash_amount, added_date):  # Added self as the first argument
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        amount = round(cash_amount/1.19)

        data = {
                "Encabezado": {
                    "IdDoc": {
                        "TipoDTE": "61",
                        "Folio": 0,
                        "FchEmis": added_date,
                        "TpoTranVenta": 1,
                        "FmaPago": "1",
                    },
                    "Emisor": {
                        "RUTEmisor": "76063822-6"
                    },
                    "Receptor": {
                        "RUTRecep": customer_data['customer_data']['rut'],
                        "RznSocRecep": customer_data['customer_data']['customer'],
                        "GiroRecep": customer_data['customer_data']['activity'],
                        "DirRecep": customer_data['customer_data']['region'],
                        "CmnaRecep": customer_data['customer_data']['commune'],
                    }
                },
                "Detalle": [
                    {
                        "NmbItem": "Nota de Crédito de Venta",
                        "QtyItem": 1,
                        "PrcItem": amount,
                        "MontoItem": amount,
                    }
                ],
                "Referencia": [ {
                    "TpoDocRef": 39,
                    "FolioRef": folio,
                    "FchRef": added_date,
                    "CodRef": 1,
                    "RazonRef": "Anula factura o boleta"
                }],
            }

        try:
            url = f"https://libredte.cl/api/dte/documentos/emitir?normalizar=1&formato=json&links=0&email=0"

            response = requests.post(
                url,
                json=data,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 200:
                try:
                    dte_data = response.json()
                except Exception:
                    return {
                        "status": "error",
                        "message": (
                            "LibreDTE emitir respondió 200 pero el cuerpo no es JSON: "
                            + (response.text[:1200] if response.text else "")
                        ),
                    }
                auth_code = dte_data.get("codigo")
                if auth_code is None or auth_code == "":
                    return {
                        "status": "error",
                        "message": (
                            "LibreDTE emitir no devolvió 'codigo': "
                            + json.dumps(dte_data, ensure_ascii=False)[:1200]
                        ),
                    }
                return auth_code

            try:
                err_body = response.json()
                detail = json.dumps(err_body, ensure_ascii=False)[:1500]
            except Exception:
                detail = (response.text[:1500] if response.text else "")
            return {
                "status": "error",
                "message": f"LibreDTE emitir rechazó ({response.status_code}): {detail}",
            }

        except Exception as e:
            print("Error al conectarse a la API:", e)
            return {"status": "error", "message": f"Error de red contra LibreDTE emitir: {str(e)}"}

    def generate_ticket(self, customer_rut, code):
        """
        Devuelve (folio, None) si OK, o (None, mensaje_error) si falla el paso generar de LibreDTE.
        """
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        data = {
            "emisor": "76063822-6",
            "receptor": customer_rut,
            "dte": 39,
            "codigo": code,
        }

        try:
            url = f"https://libredte.cl/api/dte/documentos/generar?getXML=0&links=0&email=1&retry=1&gzip=0"

            response = requests.post(
                url,
                json=data,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 200:
                try:
                    dte_data = response.json()
                except Exception:
                    return None, (
                        "LibreDTE generar respondió 200 pero el cuerpo no es JSON: "
                        + (response.text[:1200] if response.text else "")
                    )
                folio = dte_data.get("folio")
                if folio is None:
                    return None, (
                        "LibreDTE generar no devolvió 'folio': "
                        + json.dumps(dte_data, ensure_ascii=False)[:1200]
                    )
                return folio, None

            try:
                err_body = response.json()
                detail = json.dumps(err_body, ensure_ascii=False)[:1500]
            except Exception:
                detail = response.text[:1500] if response.text else ""
            err_msg = f"LibreDTE generar ({response.status_code}): {detail}"
            print("Error al generar el DTE:", err_msg)
            return None, err_msg

        except Exception as e:
            print("Error al conectarse a la API:", e)
            return None, f"Error de red contra LibreDTE generar: {str(e)}"

    def generate_credit_note_ticket(self, customer_rut, code):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        data = {
            "emisor": "76063822-6",
            "receptor": customer_rut,
            "dte": 61,
            "codigo": code
        }

        try:
            # Endpoint para generar un DTE temporal
            url = f"https://libredte.cl/api/dte/documentos/generar?getXML=0&links=0&email=1&retry=1&gzip=0"
            
            # Enviar solicitud a la API
            response = requests.post(
                url,
                json=data,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )
            
            # Manejar la respuesta
            print(response)

            if response.status_code == 200:
                dte_data = response.json()
                folio = dte_data.get("folio")

                return folio
            else:
                print("Error al generar el DTE:")
                print(response.status_code, response.json())
                return None

        except Exception as e:
            print("Error al conectarse a la API:", e)
            return None
        
    def download(self, id):
        dte = self.db.query(DteModel).filter(DteModel.id == id).first()
        if not dte or not dte.folio:
            return None

        if _is_simplefactura_v2_dte(self.db, dte):
            pdf_result = self.save_simplefactura_pdf_ticket(
                dte.folio,
                dte_type_id=int(dte.dte_type_id or 39),
            )
            if pdf_result.get("status") != "success":
                print(
                    f"[download] SimpleFactura PDF folio={dte.folio} failed: {pdf_result}",
                    flush=True,
                )
                return None
            remote_path = f"{int(dte.folio)}.pdf"
            try:
                file_contents = self.file_class.download(remote_path)
            except HTTPException as exc:
                print(f"[download] SimpleFactura PDF folio={dte.folio} file error: {exc}", flush=True)
                return None
            return {
                "file_name": f"{dte.folio}.pdf",
                "file_data": base64.b64encode(file_contents).decode("utf-8"),
            }

        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
        dte_type_id = int(dte.dte_type_id or 39)
        url = (
            f"https://libredte.cl/api/dte/dte_emitidos/pdf/{dte_type_id}/"
            f"{dte.folio}/76063822-6?formato=general&papelContinuo=0&copias_tributarias=1"
            f"&copias_cedibles=1&cedible=0&compress=0&base64=0"
        )

        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
            },
            timeout=60,
        )

        if response.status_code == 200:
            pdf_content = response.content
            timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            unique_id = uuid.uuid4().hex[:8]
            unique_filename = f"{timestamp}_{unique_id}.pdf"
            remote_path = unique_filename

            self.file_class.temporal_upload(pdf_content, remote_path)
            file_contents = self.file_class.download(remote_path)
            encoded_file = base64.b64encode(file_contents).decode("utf-8")
            self.file_class.delete(remote_path)

            return {
                "file_name": unique_filename,
                "file_data": encoded_file,
            }

        print(
            f"[download] LibreDTE PDF folio={dte.folio} type={dte_type_id} "
            f"HTTP {response.status_code}",
            flush=True,
        )
        return None
            
    def verify(self, id):
        dte = self.db.query(DteModel).filter(DteModel.id == id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        # Actualizar campos
        dte.status_id = 2
        self.db.commit()
        self.db.refresh(dte)
    
    def pre_accept(self, id):
        dte = self.db.query(DteModel).filter(DteModel.id == id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        # Actualizar campos
        dte.status_id = 2
        self.db.commit()
        self.db.refresh(dte)

    def check_payments(self):
        dtes = self.db.query(DteModel).filter(DteModel.status_id == 4).filter(DteModel.dte_type_id  == 39).filter(DteModel.dte_version_id == 1).all()

        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        for dte in dtes:
            print(f"Verificando DTE tipo 39 folio: {dte.folio}")

            url = f"https://libredte.cl/api/dte/dte_emitidos/cobro/39/{dte.folio}/76063822?getDocumento=0&getDetalle=0&getLinks=0"
                
            response = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )
            print(response.text)

            if response.status_code == 200:
                data = json.loads(response.text)
                print(data)

                payment_status = data.get("pagado")
                payment_date = data.get("pagado")
                amount = data.get("total")
                datos_json = data.get("datos")

                # Verificar si está pagado - puede venir como None, null, "none", "null", o string vacío
                is_paid = False
                if payment_status is not None and payment_status != "" and str(payment_status).lower() not in ["none", "null"]:
                    is_paid = True

                if is_paid:
                    print('DTE está pagado. Procesando...')
                    
                    # Extraer authorizationCode de datos JSON
                    authorization_code = None
                    if datos_json:
                        try:
                            datos_dict = json.loads(datos_json)
                            detail_output = datos_dict.get("detailOutput", {})
                            authorization_code = detail_output.get("authorizationCode")
                        except:
                            pass

                    if dte.status_id == 4:
                        print('Actualizando DTE...')
                        dte.expense_type_id = 25
                        dte.payment_type_id = 2
                        dte.card_amount = amount
                        dte.payment_date = payment_date
                        dte.status_id = 5
                        dte.updated_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                        
                        if authorization_code:
                            dte.comment = f"Código de autorización: {authorization_code}"

                        self.db.commit()
                        self.db.refresh(dte)

                        print(f"Dte actualizado correctamente: {dte.folio}")

                        WhatsappClass(self.db).notify_payment(dte.folio)

    # --- Emisión v2 (invoiceV2 gateway, dte_version_id = 1) ---

    def create_simplefactura_token(self):
        url = "https://api.simplefactura.cl/token"
        headers = {"Content-Type": "application/json"}
        payload = {
            "email": "jesuscova@jisparking.com",
            "password": "Jgames88!",
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("accessToken")
            SettingClass(self.db).update_token(access_token)
            return access_token
        return None

    def check_simplefactura_token(self):
        setting_data = SettingClass(self.db).get()
        token = setting_data["setting_data"]["simplefactura_token"]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        url = "https://api.simplefactura.cl/token/expire"
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 401:
            return 0
        if response.status_code == 429:
            return 2
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            return 3

    def fetch_simplefactura_token_from_jisbackend(self):
        """Token v2 desde jisbackend.com/api/settings/get_token."""
        response = requests.get(JISBACKEND_SETTINGS_TOKEN_URL, timeout=15)
        if response.status_code != 200:
            raise ValueError(
                f"jisbackend get_token HTTP {response.status_code}: {(response.text or '')[:200]}"
            )
        body = response.json()
        message = body.get("message")
        if not isinstance(message, dict):
            raise ValueError("jisbackend get_token: respuesta sin message")
        token = message.get("simplefactura_token")
        if not token:
            raise ValueError("jisbackend get_token: simplefactura_token vacío")
        SettingClass(self.db).update_token(token)
        return token

    def get_token(self):
        """Token para emisión v2 (invoiceV2)."""
        try:
            token = self.fetch_simplefactura_token_from_jisbackend()
            return {
                "status": "success",
                "accessToken": token,
                "source": "jisbackend.com",
                "renewed": False,
            }
        except (ValueError, requests.RequestException) as exc:
            return {"status": "error", "message": str(exc)}

    def check_token(self):
        check = self.check_simplefactura_token()
        if check == 0:
            return {"status": "expired", "message": "Token v2 vencido"}
        if check == 2:
            return {"status": "rate_limited", "message": "Rate limit al verificar token v2"}
        if check == 3:
            return {"status": "unknown", "message": "No se pudo verificar token v2"}
        return {"status": "valid", "expire_info": check}

    def emit_invoice_v2(self, document, branch, dte_label="DTE"):
        """POST invoiceV2 (misma capa que pre_generate_ticket / generate_ticket en LibreDTE)."""
        forced = (os.getenv("DTE_V2_FORCE_TOKEN") or os.getenv("SIMPLEFACTURA_FORCE_TOKEN") or "").strip()
        if forced:
            token = forced
        else:
            result = self.get_token()
            if result.get("status") != "success":
                return {"status": "error", "message": result.get("message") or "No se pudo obtener token v2"}
            token = result.get("accessToken")
            if not token:
                return {"status": "error", "message": "Token v2 vacío"}

        default_branch = (
            os.getenv("DTE_V2_SUCURSAL") or os.getenv("SIMPLEFACTURA_SUCURSAL") or "Casa_Matriz"
        ).strip() or "Casa_Matriz"

        # Gateway v2 invoiceV2 URL uses the registered branch slug (Casa_Matriz).
        # The parking location is sent in Emisor.CdgSIISucur via ticket_v2_issuer(branch).
        branch_office_name = v2_invoice_branch_display(branch)
        branch_slug = default_branch
        url = f"https://api.simplefactura.cl/invoiceV2/{branch_slug}"
        payload = {"Documento": document}
        payload_json = json.dumps(payload, ensure_ascii=False, indent=2)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        print(
            f"[v2] URL: {url} (sf_branch={branch_slug}, branch_office={branch_office_name or 'n/a'})",
            flush=True,
        )
        print(f"[v2] JSON payload:\n{payload_json}", flush=True)

        t0 = time.time()
        try:
            response = requests.post(
                url,
                data=json.dumps(payload, ensure_ascii=False),
                headers=headers,
                timeout=DTE_V2_HTTP_TIMEOUT,
            )
        except requests.Timeout:
            print(f"[v2] timeout after {time.time() - t0:.2f}s", flush=True)
            return {
                "status": "error",
                "message": f"Emisión v2 no respondió a tiempo ({DTE_V2_HTTP_TIMEOUT}s)",
                "v2_url": url,
            }
        except requests.RequestException as exc:
            return {"status": "error", "message": f"Error de conexión emisión v2: {exc}", "v2_url": url}

        if response.status_code == 401:
            try:
                token = self.fetch_simplefactura_token_from_jisbackend()
                response = requests.post(
                    url,
                    data=json.dumps(payload, ensure_ascii=False),
                    headers={**headers, "Authorization": f"Bearer {token}"},
                    timeout=DTE_V2_HTTP_TIMEOUT,
                )
            except (ValueError, requests.RequestException) as exc:
                return {"status": "error", "message": f"No se pudo refrescar token v2: {exc}", "v2_url": url}

        text = (response.text or "").strip()
        try:
            body = response.json() if text else {"raw": ""}
            if not isinstance(body, dict):
                body = {"raw": text[:500]}
        except ValueError:
            body = {"raw": text[:500]}

        print(f"[v2] HTTP {response.status_code} in {time.time() - t0:.2f}s", flush=True)

        if response.status_code >= 400:
            msg = body.get("message") if isinstance(body, dict) else text[:500]
            errors = body.get("errors") if isinstance(body, dict) else None
            return {
                "status": "error",
                "http_status": response.status_code,
                "message": f"Emisión v2 HTTP {response.status_code}: {msg or errors}",
                "errors": errors,
                "response": body,
                "v2_url": url,
            }

        if isinstance(body, dict) and body.get("status") not in (None, 200):
            return {
                "status": "error",
                "http_status": response.status_code,
                "message": body.get("message") or "Emisión v2 rechazada",
                "errors": body.get("errors"),
                "response": body,
                "v2_url": url,
            }

        folio = None
        data = body.get("data") if isinstance(body, dict) else None
        if isinstance(data, dict):
            for key in ("folio", "Folio", "folioDte", "FolioDTE"):
                if data.get(key) is not None:
                    folio = data.get(key)
                    break
        if folio is None and isinstance(body, dict):
            for key in ("folio", "Folio"):
                if body.get(key) is not None:
                    folio = body.get(key)
                    break

        return {
            "status": "success",
            "http_status": response.status_code,
            "message": body.get("message") if isinstance(body, dict) else f"{dte_label} emitido",
            "folio": folio,
            "data": data,
            "response": body,
            "v2_url": url,
            "v2_branch": branch_slug,
            "v2_branch_slug": branch_slug,
            "v2_branch_office": branch_office_name or None,
        }

    def _build_subscriber_credit_note_document_v2(
        self,
        customer_data,
        branch,
        *,
        ref_dte_type,
        ref_folio,
        ref_date,
        gross_amount,
        nc_folio,
    ):
        receiver = self._ticket_receiver_from_customer(customer_data)
        ref_date_str = v2_dte_api_date(ref_date)
        issue_date = v2_dte_api_date()
        gross = int(abs(gross_amount))
        net = round(gross / 1.19)
        tax = gross - net
        return {
            "Encabezado": {
                "IdDoc": {
                    "TipoDTE": 61,
                    "FchEmis": issue_date,
                    "Folio": int(nc_folio),
                },
                "Emisor": ticket_v2_issuer(branch),
                "Receptor": receiver,
                "Totales": {
                    "MntNeto": net,
                    "IVA": tax,
                    "MntTotal": gross,
                },
            },
            "Detalle": [
                {
                    "NroLinDet": "1",
                    "IndExe": 0,
                    "NmbItem": "Nota de Crédito de Venta",
                    "QtyItem": "1",
                    "PrcItem": net,
                    "MontoItem": net,
                }
            ],
            "Referencia": [
                {
                    "NroLinRef": 1,
                    "TpoDocRef": str(ref_dte_type),
                    "FolioRef": str(ref_folio),
                    "FchRef": ref_date_str,
                    "CodRef": 1,
                    "RazonRef": "Anula factura o boleta",
                }
            ],
        }

    def emit_credit_note_v2(self, document, branch, dte_label="Nota de crédito"):
        """POST invoiceCreditDebitNotesV2 (NC tipo 61, gateway v2)."""
        forced = (os.getenv("DTE_V2_FORCE_TOKEN") or os.getenv("SIMPLEFACTURA_FORCE_TOKEN") or "").strip()
        if forced:
            token = forced
        else:
            result = self.get_token()
            if result.get("status") != "success":
                return {"status": "error", "message": result.get("message") or "No se pudo obtener token v2"}
            token = result.get("accessToken")
            if not token:
                return {"status": "error", "message": "Token v2 vacío"}

        default_branch = (
            os.getenv("DTE_V2_SUCURSAL") or os.getenv("SIMPLEFACTURA_SUCURSAL") or "Casa_Matriz"
        ).strip() or "Casa_Matriz"
        branch_office_name = v2_invoice_branch_display(branch)
        branch_slug = default_branch
        url = f"https://api.simplefactura.cl/invoiceCreditDebitNotesV2/{branch_slug}/6"
        payload = {"Documento": document}
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        print(
            f"[v2-nc] URL: {url} (sf_branch={branch_slug}, branch_office={branch_office_name or 'n/a'})",
            flush=True,
        )
        print(f"[v2-nc] JSON payload:\n{json.dumps(payload, ensure_ascii=False, indent=2)}", flush=True)

        t0 = time.time()
        try:
            response = requests.post(
                url,
                data=json.dumps(payload, ensure_ascii=False),
                headers=headers,
                timeout=DTE_V2_HTTP_TIMEOUT,
            )
        except requests.Timeout:
            return {
                "status": "error",
                "message": f"NC v2 no respondió a tiempo ({DTE_V2_HTTP_TIMEOUT}s)",
                "v2_url": url,
            }
        except requests.RequestException as exc:
            return {"status": "error", "message": f"Error de conexión NC v2: {exc}", "v2_url": url}

        if response.status_code == 401:
            try:
                token = self.fetch_simplefactura_token_from_jisbackend()
                response = requests.post(
                    url,
                    data=json.dumps(payload, ensure_ascii=False),
                    headers={**headers, "Authorization": f"Bearer {token}"},
                    timeout=DTE_V2_HTTP_TIMEOUT,
                )
            except (ValueError, requests.RequestException) as exc:
                return {"status": "error", "message": f"No se pudo refrescar token v2: {exc}", "v2_url": url}

        text = (response.text or "").strip()
        try:
            body = response.json() if text else {"raw": ""}
            if not isinstance(body, dict):
                body = {"raw": text[:500]}
        except ValueError:
            body = {"raw": text[:500]}

        print(f"[v2-nc] HTTP {response.status_code} in {time.time() - t0:.2f}s", flush=True)

        if response.status_code >= 400:
            msg = body.get("message") if isinstance(body, dict) else text[:500]
            errors = body.get("errors") if isinstance(body, dict) else None
            return {
                "status": "error",
                "http_status": response.status_code,
                "message": f"NC v2 HTTP {response.status_code}: {msg or errors}",
                "errors": errors,
                "response": body,
                "v2_url": url,
            }

        if isinstance(body, dict) and body.get("status") not in (None, 200):
            return {
                "status": "error",
                "http_status": response.status_code,
                "message": body.get("message") or "NC v2 rechazada",
                "errors": body.get("errors"),
                "response": body,
                "v2_url": url,
            }

        folio = None
        data = body.get("data") if isinstance(body, dict) else None
        if isinstance(data, dict):
            for key in ("folio", "Folio", "folioDte", "FolioDTE"):
                if data.get(key) is not None:
                    folio = data.get(key)
                    break
        if folio is None and isinstance(body, dict):
            for key in ("folio", "Folio"):
                if body.get(key) is not None:
                    folio = body.get(key)
                    break

        return {
            "status": "success",
            "http_status": response.status_code,
            "message": body.get("message") if isinstance(body, dict) else dte_label,
            "folio": folio,
            "data": data,
            "response": body,
            "v2_url": url,
        }

    def store_credit_note_v2(self, form_data, ref_dte_type=39, negative_amounts=False):
        """
        NC v2 (gateway externo). El folio tipo 61 se reserva en tabla `folios`
        (document_type_id=61, pool central branch_office_id=0, used_id=0).
        Igual que boletas (39) y facturas (33) en generate_v2.
        """
        dte = self.db.query(DteModel).filter(DteModel.id == form_data.id).first()
        if not dte:
            return {"status": "error", "message": "DTE no encontrado"}
        if dte.status_id != 4:
            return {"status": "error", "message": "Solo se puede anular un DTE emitido (status 4)"}
        if int(dte.dte_type_id) != int(ref_dte_type):
            return {"status": "error", "message": "Tipo de DTE no coincide"}

        customer = CustomerClass(self.db).get_by_rut(dte.rut)
        customer_data = json.loads(customer)
        if "customer_data" not in customer_data:
            return {"status": "error", "message": "Cliente no encontrado"}

        branch = (
            self.db.query(BranchOfficeModel)
            .filter(BranchOfficeModel.id == dte.branch_office_id)
            .first()
        )
        if not branch:
            return {"status": "error", "message": "Sucursal no encontrada"}

        gross = int(dte.cash_amount) if dte.cash_amount else int(dte.total)
        ref_date = dte.added_date if dte.added_date else datetime.now()

        # Folio NC desde tabla folios (document_type_id=61), no desde la API.
        folio_res = FolioClass(self.db).reserve_next_by_document_type(
            61,
            branch_office_id=dte.branch_office_id,
        )
        if folio_res.get("status") != "success":
            return folio_res

        reserved_folio = int(folio_res["folio"])

        document = self._build_subscriber_credit_note_document_v2(
            customer_data,
            branch,
            ref_dte_type=ref_dte_type,
            ref_folio=dte.folio,
            ref_date=ref_date,
            gross_amount=gross,
            nc_folio=reserved_folio,
        )

        emit_result = self.emit_credit_note_v2(document, branch)
        if emit_result.get("status") != "success":
            FolioClass(self.db).release_folio_pool(folio_res["id"])
            return emit_result

        folio_number = reserved_folio

        dte.status_id = 5
        dte.reason_id = form_data.reason_id
        dte.comment = f"Folio de la Nota de Crédito {folio_number}"
        self.db.add(dte)
        self.db.commit()

        credit_note_dte = DteModel()
        credit_note_dte.branch_office_id = dte.branch_office_id
        credit_note_dte.cashier_id = dte.cashier_id if ref_dte_type == 39 else 0
        credit_note_dte.dte_type_id = 61
        credit_note_dte.dte_version_id = DTE_VERSION_V2
        credit_note_dte.status_id = 5
        credit_note_dte.chip_id = 0
        credit_note_dte.rut = customer_data["customer_data"]["rut"]
        credit_note_dte.folio = folio_number
        subtotal = round(gross / 1.19)
        tax = gross - subtotal
        if negative_amounts:
            credit_note_dte.cash_amount = -abs(gross)
            credit_note_dte.card_amount = 0
            credit_note_dte.subtotal = -abs(subtotal)
            credit_note_dte.tax = -abs(tax)
            credit_note_dte.discount = 0
            credit_note_dte.total = -abs(gross)
            credit_note_dte.period = datetime.now().strftime("%Y-%m")
            credit_note_dte.added_date = dte.added_date
        else:
            credit_note_dte.cash_amount = gross
            credit_note_dte.card_amount = 0
            credit_note_dte.subtotal = subtotal
            credit_note_dte.tax = tax
            credit_note_dte.discount = 0
            credit_note_dte.total = gross
            credit_note_dte.added_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        credit_note_dte.category_id = 1
        credit_note_dte.quantity = None

        self.db.add(credit_note_dte)
        try:
            self.db.commit()
            self.db.refresh(credit_note_dte)
            FolioClass(self.db).bind_folio_to_dte(folio_res["id"], credit_note_dte.id)
            return {"status": "success", "message": "Credit Note saved successfully"}
        except Exception as e:
            self.db.rollback()
            FolioClass(self.db).release_folio_pool(folio_res["id"])
            return {"status": "error", "message": f"Error: {str(e)}"}

    def _v2_bearer_token(self):
        forced = (os.getenv("DTE_V2_FORCE_TOKEN") or os.getenv("SIMPLEFACTURA_FORCE_TOKEN") or "").strip()
        if forced:
            return forced, None
        result = self.get_token()
        if result.get("status") != "success":
            return None, result.get("message") or "No se pudo obtener token v2"
        token = result.get("accessToken")
        if not token:
            return None, "Token v2 vacío"
        return token, None

    def send_invoice_v2_email(
        self,
        folio,
        dte_type_id=39,
        to_emails=None,
        pdf=True,
        xml=False,
        comments=None,
    ):
        """
        Envía boleta/factura por correo vía gateway v2 POST /dte/enviar/mail.
        """
        recipients = []
        if isinstance(to_emails, str):
            to_emails = [to_emails]
        if to_emails:
            recipients = [
                str(email).strip()
                for email in to_emails
                if email and str(email).strip() and "@" in str(email)
            ]
        if not recipients:
            return {"status": "skipped", "message": "Sin correo destinatario"}

        token, token_err = self._v2_bearer_token()
        if not token:
            return {"status": "error", "message": token_err}

        payload = {
            "rutEmpresa": "76063822-6",
            "dte": {
                "folio": int(folio),
                "tipoDTE": int(dte_type_id),
            },
            "mail": {
                "to": recipients,
                "ccos": [],
                "ccs": [],
            },
            "pdf": bool(pdf),
            "xml": bool(xml),
        }
        if comments:
            payload["comments"] = comments

        url = "https://api.simplefactura.cl/dte/enviar/mail"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        print(f"[v2] POST {url} folio={folio} tipo={dte_type_id} to={recipients}", flush=True)

        try:
            response = requests.post(
                url,
                data=json.dumps(payload, ensure_ascii=False),
                headers=headers,
                timeout=DTE_V2_HTTP_TIMEOUT,
            )
        except requests.Timeout:
            return {"status": "error", "message": f"Envío correo v2 no respondió a tiempo ({DTE_V2_HTTP_TIMEOUT}s)"}
        except requests.RequestException as exc:
            return {"status": "error", "message": f"Error de conexión envío correo v2: {exc}"}

        if response.status_code == 401:
            try:
                token = self.fetch_simplefactura_token_from_jisbackend()
                response = requests.post(
                    url,
                    data=json.dumps(payload, ensure_ascii=False),
                    headers={**headers, "Authorization": f"Bearer {token}"},
                    timeout=DTE_V2_HTTP_TIMEOUT,
                )
            except (ValueError, requests.RequestException) as exc:
                return {"status": "error", "message": f"No se pudo refrescar token v2 (correo): {exc}"}

        text = (response.text or "").strip()
        try:
            body = response.json() if text else {}
            if not isinstance(body, dict):
                body = {"raw": text[:500]}
        except ValueError:
            body = {"raw": text[:500]}

        print(f"[v2] email HTTP {response.status_code}: {text[:300]}", flush=True)

        if response.status_code >= 400:
            msg = body.get("message") if isinstance(body, dict) else text[:500]
            errors = body.get("errors") if isinstance(body, dict) else None
            return {
                "status": "error",
                "http_status": response.status_code,
                "message": f"Envío correo v2 HTTP {response.status_code}: {msg or errors}",
                "errors": errors,
                "response": body,
            }

        return {
            "status": "success",
            "http_status": response.status_code,
            "message": body.get("message") if isinstance(body, dict) else "Correo enviado",
            "response": body,
        }

    def save_simplefactura_pdf_ticket(self, folio, dte_type_id=39):
        """
        Descarga PDF desde gateway v2 getPdf y lo publica en /files/{folio}.pdf
        (mismo path que usa WhatsApp send() con LibreDTE).
        """
        remote_path = f"{int(folio)}.pdf"
        try:
            self.file_class.download(remote_path)
            return {
                "status": "success",
                "url": self.file_class.get(remote_path),
                "cached": True,
            }
        except HTTPException:
            pass

        token, token_err = self._v2_bearer_token()
        if not token:
            return {"status": "error", "message": token_err or "Sin token v2 para PDF"}

        payload = {
            "credenciales": {
                "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
                "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
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
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=DTE_V2_HTTP_TIMEOUT,
            )
        except requests.RequestException as exc:
            return {"status": "error", "message": f"Error getPdf v2: {exc}"}

        if response.status_code == 401:
            try:
                token = self.fetch_simplefactura_token_from_jisbackend()
                response = requests.post(
                    url,
                    json=payload,
                    headers={**headers, "Authorization": f"Bearer {token}"},
                    timeout=DTE_V2_HTTP_TIMEOUT,
                )
            except (ValueError, requests.RequestException) as exc:
                return {"status": "error", "message": f"No se pudo refrescar token v2 (PDF): {exc}"}

        if response.status_code != 200 or not response.content:
            return {
                "status": "error",
                "message": f"getPdf v2 HTTP {response.status_code}",
                "response": (response.text or "")[:500],
            }

        self.file_class.temporal_upload(response.content, remote_path)
        return {
            "status": "success",
            "url": self.file_class.get(remote_path),
            "cached": False,
        }

    def mark_simplefactura_paid_status(self, folio, dte_type_id=39, paid=True):
        """
        SimpleFactura POST /dte/marcar-pagado-pendiente — set document paid/pending flag.
        API field remains ``pagado`` (bool) per MarcarPagadoOPendienteRequest schema.
        """
        token, token_err = self._v2_bearer_token()
        if not token:
            return {"status": "error", "message": token_err or "Missing v2 token"}

        payload = {
            "credenciales": {
                "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
                "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
            },
            "dteReferenciadoExterno": {
                "folio": int(folio),
                "codigoTipoDte": int(dte_type_id),
                "ambiente": SIMPLEFACTURA_AMBIENTE,
            },
            "pagado": bool(paid),
        }
        url = "https://api.simplefactura.cl/dte/marcar-pagado-pendiente"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=DTE_V2_HTTP_TIMEOUT,
            )
        except requests.RequestException as exc:
            return {"status": "error", "message": f"mark-paid request failed: {exc}"}

        if response.status_code == 401:
            try:
                token = self.fetch_simplefactura_token_from_jisbackend()
                response = requests.post(
                    url,
                    json=payload,
                    headers={**headers, "Authorization": f"Bearer {token}"},
                    timeout=DTE_V2_HTTP_TIMEOUT,
                )
            except (ValueError, requests.RequestException) as exc:
                return {"status": "error", "message": f"Could not refresh v2 token (mark-paid): {exc}"}

        text = (response.text or "").strip()
        try:
            body = response.json() if text else {}
            if not isinstance(body, dict):
                body = {"raw": text[:500]}
        except ValueError:
            body = {"raw": text[:500]}

        if response.status_code >= 400:
            msg = body.get("message") if isinstance(body, dict) else text[:500]
            errors = body.get("errors") if isinstance(body, dict) else None
            return {
                "status": "error",
                "http_status": response.status_code,
                "message": f"mark-paid HTTP {response.status_code}: {msg or errors or text[:200]}",
                "response": body,
            }

        if isinstance(body, dict) and body.get("status") not in (None, 200, "200"):
            return {
                "status": "error",
                "http_status": response.status_code,
                "message": body.get("message") or "SimpleFactura rejected mark-paid",
                "response": body,
            }

        return {
            "status": "success",
            "http_status": response.status_code,
            "message": body.get("message") if isinstance(body, dict) else "Paid status updated",
            "response": body,
            "paid": bool(paid),
            "folio": int(folio),
        }

    def get_all_v2(self, rol_id=None, rut=None, group=1, page=0, items_per_page=10, period=None):
        return self.get_all(
            rol_id, rut, group, page, items_per_page, period,
            dte_version_id=DTE_VERSION_V2,
            include_emitted=True,
        )

    def search_v2(
        self,
        rol_id=None,
        supervisor_rut=None,
        branch_office_id=None,
        rut=None,
        customer=None,
        status_id=None,
        supervisor_id=None,
        page=0,
        items_per_page=10,
        category_id=None,
    ):
        return self.search(
            rol_id,
            supervisor_rut,
            branch_office_id,
            rut,
            customer,
            status_id,
            supervisor_id,
            page,
            items_per_page,
            category_id,
            dte_version_id=DTE_VERSION_V2,
            include_emitted=True,
        )

    def store_v2(self, form_data, rol_id):
        if form_data.will_save != 1:
            return "error"

        dte = DteModel()
        period = datetime.now().strftime("%Y-%m")
        if rol_id == 1 or rol_id == 2:
            status_id = 2
        elif rol_id == 4:
            status_id = 1
        else:
            status_id = 1

        dte.branch_office_id = form_data.branch_office_id
        dte.cashier_id = 0
        dte.dte_type_id = 39
        dte.dte_version_id = DTE_VERSION_V2
        dte.status_id = status_id
        dte.rut = form_data.rut
        dte.folio = 0
        cid = getattr(form_data, "category_id", None)
        dte.category_id = cid if cid is not None else 1
        chip = int(form_data.chip_id or 0)
        if dte.category_id == 3:
            chip = 0
        dte.chip_id = chip
        group_items = self._normalize_group_items(getattr(form_data, "items", []))
        _apply_ticket_draft_amounts(dte, form_data, pxq_items=group_items if group_items else None)
        dte.period = period
        dte.added_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        qty = getattr(form_data, "quantity", None)
        if dte.category_id == 3 and group_items:
            dte.quantity = sum(item["quantity"] for item in group_items)
        elif dte.category_id == 3 and qty is not None:
            dte.quantity = int(qty)
        else:
            dte.quantity = None

        self.db.add(dte)
        try:
            self.db.flush()
            if dte.category_id == 3 and group_items:
                self._replace_ticket_items(dte.id, group_items)
            self.db.commit()
            return {"status": "success", "message": "Dte saved successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}

    def test_emit_biller_style_v2(self, total=700, item_label="Estacionamiento 113 - 918", branch_office_id=1):
        """Prueba invoiceV2 biller (Bearer, Folio desde tabla folios)."""
        branch = (
            self.db.query(BranchOfficeModel)
            .filter(BranchOfficeModel.id == branch_office_id)
            .first()
        )
        folio_res = FolioClass(self.db).reserve_next_by_document_type(39, branch_office_id=branch_office_id)
        if folio_res.get("status") != "success":
            return folio_res

        issue_date = v2_dte_api_date()
        due_date = v2_dte_api_date(datetime.now() + timedelta(days=30))
        subtotal = round(total / 1.19)
        tax = total - subtotal
        document = {
            "Encabezado": {
                "IdDoc": {
                    "TipoDTE": 39,
                    "FchEmis": issue_date,
                    "FchVenc": due_date,
                    "Folio": int(folio_res["folio"]),
                    "IndServicio": 3,
                    "IndMntNeto": 2,
                },
                "Emisor": ticket_v2_issuer(branch),
                "Receptor": {
                    "RUTRecep": "66666666-6",
                    "RznSocRecep": "Cliente en Sucursal",
                },
                "Totales": {
                    "MntNeto": subtotal,
                    "IVA": tax,
                    "MntTotal": total,
                },
            },
            "Detalle": [
                {
                    "NroLinDet": "1",
                    "NmbItem": item_label,
                    "QtyItem": "1",
                    "UnmdItem": "un",
                    "PrcItem": subtotal,
                    "MontoItem": subtotal,
                }
            ],
        }
        emit_result = self.emit_invoice_v2(document, branch, "Boleta biller test")
        if emit_result.get("status") != "success":
            FolioClass(self.db).release_folio_pool(folio_res["id"])
        return emit_result

    def test_emit_ticket_v2(self, form_data):
        branch = (
            self.db.query(BranchOfficeModel)
            .filter(BranchOfficeModel.id == form_data.branch_office_id)
            .first()
        )
        if not branch:
            return {"status": "error", "message": "Sucursal no encontrada"}

        customer = CustomerClass(self.db).get_by_rut(form_data.rut)
        customer_data = json.loads(customer)
        if "customer_data" not in customer_data:
            return {"status": "error", "message": "Cliente no encontrado"}

        folio_res = FolioClass(self.db).reserve_next_by_document_type(
            39,
            branch_office_id=getattr(form_data, "branch_office_id", None),
            dte_id=getattr(form_data, "id", None),
        )
        if folio_res.get("status") != "success":
            return folio_res

        source_dte = self._ticket_source_dte_from_form(form_data)
        detail_lines = self._ticket_pre_detalle_lines_from_form(form_data, source_dte)
        if isinstance(detail_lines, dict) and detail_lines.get("status") == "error":
            FolioClass(self.db).release_folio_pool(folio_res["id"])
            return detail_lines

        category_id = getattr(form_data, "category_id", None)
        if category_id is None and source_dte is not None:
            category_id = source_dte.category_id
        category_id = int(category_id or 1)

        formatted_lines, total_gross = self._v2_format_detalle_lines(detail_lines, category_id)

        cd = customer_data["customer_data"]
        receiver = {
            "RUTRecep": (getattr(form_data, "rut", None) or cd.get("rut") or "").strip(),
            "RznSocRecep": (
                (getattr(form_data, "customer", None) or cd.get("customer") or cd.get("rut") or "")
            ).strip(),
        }
        address = getattr(form_data, "address", None) or cd.get("address") or cd.get("region")
        if address:
            receiver["DirRecep"] = str(address).strip()
        commune = cd.get("commune")
        if commune:
            receiver["CmnaRecep"] = str(commune).strip()
        email = getattr(form_data, "email", None) or cd.get("email")
        if email:
            email = str(email).strip()
            receiver["CorreoRecep"] = email
            receiver["Contacto"] = email
        phone = getattr(form_data, "phone", None) or cd.get("phone")
        if phone:
            receiver["TelefonoRecep"] = str(phone).strip()

        issue_date = v2_dte_api_date()
        due_date = v2_dte_api_date(datetime.now() + timedelta(days=30))
        net_amount = round(total_gross / 1.19)
        tax_amount = total_gross - net_amount
        document = {
            "Encabezado": {
                "IdDoc": {
                    "TipoDTE": 39,
                    "FchEmis": issue_date,
                    "FchVenc": due_date,
                    "Folio": int(folio_res["folio"]),
                    "IndServicio": 3,
                    "IndMntNeto": 2,
                },
                "Emisor": ticket_v2_issuer(branch),
                "Receptor": receiver,
                "Totales": {
                    "MntNeto": net_amount,
                    "IVA": tax_amount,
                    "MntTotal": total_gross,
                },
            },
            "Detalle": formatted_lines,
        }

        emit_result = self.emit_invoice_v2(document, branch, "Boleta")
        if emit_result.get("status") != "success":
            FolioClass(self.db).release_folio_pool(folio_res["id"])
        return emit_result

    def _resolve_v2_ticket_draft(self, form_data, expected_total_doc):
        """Borrador v2 en dtes (status 1 o 2, folio 0) para actualizar al emitir."""
        period_str = datetime.now().strftime("%Y-%m")
        rut_clause = dte_rut_sql_or(DteModel.rut, form_data.rut)

        form_dte_id = getattr(form_data, "id", None)
        if form_dte_id not in (None, "", 0):
            try:
                form_dte_id = int(form_dte_id)
            except (TypeError, ValueError):
                form_dte_id = None
        if form_dte_id:
            dte = (
                self.db.query(DteModel)
                .filter(
                    DteModel.id == form_dte_id,
                    DteModel.dte_type_id == 39,
                    DteModel.dte_version_id.in_((DTE_VERSION_V2, DTE_VERSION_V2_LEGACY)),
                    DteModel.status_id.in_((1, 2)),
                )
                .first()
            )
            if dte is not None:
                return dte

        def _find_draft(require_total: bool):
            q = self.db.query(DteModel).filter(
                DteModel.branch_office_id == form_data.branch_office_id,
                rut_clause,
                DteModel.dte_type_id == 39,
                DteModel.dte_version_id.in_((DTE_VERSION_V2, DTE_VERSION_V2_LEGACY)),
                DteModel.status_id.in_((1, 2)),
                DteModel.period == period_str,
                DteModel.folio == 0,
            )
            if require_total:
                q = q.filter(DteModel.total == expected_total_doc)
            return q.order_by(DteModel.id.desc()).first()

        dte = _find_draft(True) or _find_draft(False)
        if dte is not None:
            return dte

        return (
            self.db.query(DteModel)
            .filter(
                DteModel.branch_office_id == form_data.branch_office_id,
                rut_clause,
                DteModel.dte_type_id == 39,
                DteModel.dte_version_id.in_((DTE_VERSION_V2, DTE_VERSION_V2_LEGACY)),
                DteModel.status_id.in_((1, 2)),
                DteModel.period == period_str,
            )
            .order_by(DteModel.id.desc())
            .first()
        )

    def generate_v2(self, form_data):
        print(
            f"[v2] generate_v2 rut={form_data.rut} branch={form_data.branch_office_id}",
            flush=True,
        )
        expected_total_doc = self._expected_total_for_generate(form_data)
        check_dte_existence = (
            self.db.query(DteModel)
            .filter(
                DteModel.branch_office_id == form_data.branch_office_id,
                DteModel.rut == form_data.rut,
                DteModel.total == expected_total_doc,
                DteModel.dte_type_id == 39,
                DteModel.dte_version_id.in_((DTE_VERSION_V2, DTE_VERSION_V2_LEGACY)),
                DteModel.status_id == 4,
                DteModel.period == datetime.now().strftime("%Y-%m"),
            )
            .count()
        )
        if check_dte_existence != 0:
            return {
                "status": "error",
                "message": "Dte already exists for this RUT in the current period",
            }

        customer = CustomerClass(self.db).get_by_rut(form_data.rut)
        customer_data = json.loads(customer)
        if "customer_data" not in customer_data:
            return {"status": "error", "message": "Cliente no encontrado"}

        branch = (
            self.db.query(BranchOfficeModel)
            .filter(BranchOfficeModel.id == form_data.branch_office_id)
            .first()
        )
        if not branch:
            return {"status": "error", "message": "Sucursal no encontrada"}

        dte = self._resolve_v2_ticket_draft(form_data, expected_total_doc)
        if not dte:
            return {
                "status": "error",
                "message": "No hay borrador v2 en dtes para emitir (status 1 o 2, folio 0).",
            }

        folio_res = FolioClass(self.db).reserve_next_by_document_type(
            39,
            branch_office_id=getattr(form_data, "branch_office_id", None),
            dte_id=dte.id,
        )
        if folio_res.get("status") != "success":
            return folio_res

        source_dte = self._ticket_source_dte_from_form(form_data) or dte
        detail_lines = self._ticket_pre_detalle_lines_from_form(form_data, source_dte)
        if isinstance(detail_lines, dict) and detail_lines.get("status") == "error":
            FolioClass(self.db).release_folio_pool(folio_res["id"])
            return detail_lines

        category_id = getattr(form_data, "category_id", None)
        if category_id is None and source_dte is not None:
            category_id = source_dte.category_id
        category_id = int(category_id or 1)

        formatted_lines, total_gross = self._v2_format_detalle_lines(detail_lines, category_id)

        cd = customer_data["customer_data"]
        receiver = {
            "RUTRecep": (getattr(form_data, "rut", None) or cd.get("rut") or "").strip(),
            "RznSocRecep": (
                (getattr(form_data, "customer", None) or cd.get("customer") or cd.get("rut") or "")
            ).strip(),
        }
        address = getattr(form_data, "address", None) or cd.get("address") or cd.get("region")
        if address:
            receiver["DirRecep"] = str(address).strip()
        commune = cd.get("commune")
        if commune:
            receiver["CmnaRecep"] = str(commune).strip()
        email = getattr(form_data, "email", None) or cd.get("email")
        if email:
            email = str(email).strip()
            receiver["CorreoRecep"] = email
            receiver["Contacto"] = email
        phone = getattr(form_data, "phone", None) or cd.get("phone")
        if phone:
            receiver["TelefonoRecep"] = str(phone).strip()

        base_date = dte.added_date if dte.added_date else datetime.now()
        issue_date = v2_dte_api_date(base_date)
        due_date = v2_dte_api_date(base_date + timedelta(days=30))
        net_amount = round(total_gross / 1.19)
        tax_amount = total_gross - net_amount
        document = {
            "Encabezado": {
                "IdDoc": {
                    "TipoDTE": 39,
                    "FchEmis": issue_date,
                    "FchVenc": due_date,
                    "Folio": int(folio_res["folio"]),
                    "IndServicio": 3,
                    "IndMntNeto": 2,
                },
                "Emisor": ticket_v2_issuer(branch),
                "Receptor": receiver,
                "Totales": {
                    "MntNeto": net_amount,
                    "IVA": tax_amount,
                    "MntTotal": total_gross,
                },
            },
            "Detalle": formatted_lines,
        }

        emit_result = self.emit_invoice_v2(document, branch, "Boleta")

        print(f"[v2] emit_result status={emit_result.get('status')}", flush=True)

        if emit_result.get("status") != "success":
            FolioClass(self.db).release_folio_pool(folio_res["id"])
            return {
                "status": "error",
                "message": emit_result.get("message") or "Emisión v2 no emitió la boleta",
                "errors": emit_result.get("errors"),
                "response": emit_result.get("response"),
                "v2_url": emit_result.get("v2_url"),
                "v2_payload": {"Documento": document},
            }

        folio_number = int(folio_res["folio"])

        dte.folio = folio_number
        dte.status_id = 4
        dte.dte_version_id = DTE_VERSION_V2
        dte.updated_date = datetime.now()
        group_items = self._get_group_items_for_generation(form_data, dte)
        cid = int(getattr(form_data, "category_id", None) or dte.category_id or 1)
        chip = int(getattr(form_data, "chip_id", 0) or 0)
        if cid == 3:
            chip = 0
        dte.chip_id = chip
        dte.category_id = cid
        _set_dte_gross_totals(dte, total_gross)
        if cid == 3:
            if group_items:
                dte.quantity = sum(item["quantity"] for item in group_items)
                if self._normalize_group_items(getattr(form_data, "items", [])):
                    self._replace_ticket_items(dte.id, group_items)
            elif getattr(form_data, "quantity", None) is not None:
                dte.quantity = int(form_data.quantity)

        try:
            self.db.commit()
            self.db.refresh(dte)
            FolioClass(self.db).bind_folio_to_dte(folio_res["id"], dte.id)

            from app.backend.classes.dte_subscriber_email_class import DteSubscriberEmailClass

            recipient_email = (getattr(form_data, "email", None) or cd.get("email") or "").strip()
            customer_obj = (
                self.db.query(CustomerModel)
                .filter(CustomerModel.rut == form_data.rut)
                .first()
            )
            email_result = DteSubscriberEmailClass(self.db).send(
                dte,
                customer=customer_obj,
                to_emails=recipient_email,
            )

            print("Empieza envio de whatsapp v2 (payments)", flush=True)
            whatsapp_result = WhatsappClass(self.db).send_v2_invoice(dte, form_data.rut)
            print(f"[v2] whatsapp_result folio={dte.folio}: {whatsapp_result}", flush=True)

            return {
                "status": "success",
                "message": "Dte saved successfully",
                "dte_id": dte.id,
                "folio": dte.folio,
                "status_id": dte.status_id,
                "response": emit_result.get("response"),
                "email": email_result,
                "whatsapp": whatsapp_result,
            }
        except Exception as e:
            self.db.rollback()
            FolioClass(self.db).release_folio_pool(folio_res["id"])
            return {"status": "error", "message": f"Error: {str(e)}"}


