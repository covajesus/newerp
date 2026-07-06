from sqlalchemy.orm import Session
from app.backend.db.models import DteModel, DteReferenceModel, CustomerDteItemModel, CustomerModel, BranchOfficeModel, UserModel, ExpenseTypeModel
from app.backend.classes.customer_class import CustomerClass
from app.backend.classes.whatsapp_class import WhatsappClass
from app.backend.classes.helper_class import HelperClass, dte_rut_sql_or
from app.backend.classes.file_class import FileClass
import requests
from datetime import datetime
import json
from sqlalchemy import desc
from sqlalchemy.dialects import mysql
import uuid
import base64
from sqlalchemy import or_
from fastapi import HTTPException
from app.backend.classes.libredte_dte_lines import libredte_detail_line_from_group_item
from app.backend.classes.customer_ticket_class import CustomerTicketClass, DTE_VERSION_V2, ticket_v2_issuer, v2_dte_api_date
from app.backend.classes.customer_ticket_class import (
    DTE_CHIP_AMOUNT_CLP,
    _set_dte_gross_totals,
    document_gross_from_form,
)
from app.backend.classes.folio_class import FolioClass
from datetime import timedelta
from app.backend.classes.dte_pxq_amounts import dte_totals_from_net, pxq_net_total_from_items


def _bill_total_from_form(form_data, dte_row=None):
    """Amount for draft lookup / emit. Cat 2: net; cat 3 group: gross; cat 1: gross (± chip)."""
    cid = getattr(form_data, "category_id", None)
    if cid is None and dte_row is not None:
        cid = getattr(dte_row, "category_id", None)
    cid = int(cid or 1)
    if cid == 2:
        return int(form_data.amount)
    if cid == 3:
        return int(form_data.amount)
    if getattr(form_data, "chip_id", None) != 1:
        return int(form_data.amount)
    if getattr(form_data, "will_save", 0) == 1:
        return int(form_data.amount) + 5000
    return int(form_data.amount)


def _bill_parking_for_dte_match(form_data, dte_row=None):
    """Estacionamiento (dtes.total) para buscar borrador o DTE emitido."""
    cid = getattr(form_data, "category_id", None)
    if cid is None and dte_row is not None:
        cid = getattr(dte_row, "category_id", None)
    cid = int(cid or 1)
    if cid == 2:
        return int(_bill_total_from_form(form_data, dte_row))
    if cid == 3:
        return int(_bill_total_from_form(form_data, dte_row))
    return int(form_data.amount)


def _bill_gross_for_dte_match(form_data, dte_row=None):
    """Alias: estacionamiento en dtes.total (chip_id indica +$5.000 al pagar)."""
    return _bill_parking_for_dte_match(form_data, dte_row)


def _apply_bill_draft_amounts(dte, form_data, pxq_items=None):
    """Persist draft amounts. Cat 2: neto; cat 3: bruto en form, neto desde líneas si hay PXQ."""
    cid = getattr(form_data, "category_id", None)
    if cid is None:
        cid = getattr(dte, "category_id", None)
    cid = int(cid or 1)
    chip = int(getattr(form_data, "chip_id", 0) or 0)
    if cid == 3:
        chip = 0

    raw = int(form_data.amount)
    pxq_net = pxq_net_total_from_items(pxq_items)

    dte.discount = 0
    dte.chip_id = chip
    dte.category_id = cid

    if cid == 3:
        if pxq_net is not None:
            net, tax, gross, cash = dte_totals_from_net(pxq_net)
        else:
            gross = raw
            net = round(gross / 1.19)
            tax = gross - net
            cash = gross
        dte.subtotal = net
        dte.total = gross
        dte.tax = tax
        dte.cash_amount = cash
        return

    if cid == 2:
        net = pxq_net if pxq_net is not None else raw
        _, tax, gross, cash = dte_totals_from_net(net)
        dte.subtotal = net
        dte.total = gross
        dte.tax = tax
        dte.cash_amount = cash
        return

    gross = document_gross_from_form(form_data)
    parking = int(form_data.amount)
    dte.cash_amount = gross
    dte.subtotal = round(gross / 1.19)
    dte.tax = gross - dte.subtotal
    dte.total = parking


def _sync_bill_dte_amounts_from_form(dte, form_data, pxq_items=None):
    """
    Al emitir folio, fijar montos en dtes.
    Cat 2/3 con líneas PXQ: subtotal = suma neta, IVA = total − neto, cash_amount/total = bruto.
    """
    cid = getattr(form_data, "category_id", None)
    if cid is None:
        cid = getattr(dte, "category_id", None)
    cid = int(cid or 1)

    dte.chip_id = form_data.chip_id
    pxq_net = pxq_net_total_from_items(pxq_items)

    if cid == 3:
        dte.chip_id = 0
        if pxq_net is not None:
            net, tax, gross, cash = dte_totals_from_net(pxq_net)
        else:
            gross = int(_bill_total_from_form(form_data))
            net = round(gross / 1.19)
            tax = gross - net
            cash = gross
        dte.cash_amount = cash
        dte.subtotal = net
        dte.total = gross
        dte.tax = tax
        dte.category_id = cid
    elif cid == 2:
        net = pxq_net if pxq_net is not None else int(_bill_total_from_form(form_data))
        _, tax, gross, cash = dte_totals_from_net(net)
        dte.cash_amount = cash
        dte.subtotal = net
        dte.total = gross
        dte.tax = tax
        dte.category_id = cid
    else:
        gross = document_gross_from_form(form_data)
        parking = int(form_data.amount)
        _set_dte_gross_totals(dte, gross)
        dte.total = parking
        dte.category_id = cid

    qty = getattr(form_data, "quantity", None)
    if qty is not None:
        dte.quantity = int(qty)


def _bill_category_id(form_data, dte_row):
    """category_id en dtes: 1 normal, 2 con referencias SII, 3 factura grupal (múltiples ítems)."""
    cid = getattr(form_data, "category_id", None)
    if cid is None and dte_row is not None:
        cid = getattr(dte_row, "category_id", None)
    return cid


def _folio_ref_for_oc(oc_reference_str):
    """FolioRef SII: numérico si aplica; si no, cadena."""
    if not oc_reference_str:
        return 0
    s = str(oc_reference_str).strip()
    if not s:
        return 0
    try:
        return int(s)
    except ValueError:
        return s


def _reference_line_to_dict(line):
    if line is None:
        return {}
    if hasattr(line, "model_dump"):
        return line.model_dump()
    return dict(line)


def _reference_line_nonempty(d):
    if not d:
        return False
    for k in ("reference_type_id", "reference_date_id", "reference_code", "reference_description"):
        v = d.get(k)
        if v is not None and str(v).strip() not in ("", "null", "None"):
            return True
    return False


def _reference_value_is_date_like(value) -> bool:
    if value is None:
        return False
    s = str(value).strip()
    if not s or s.lower() in ("null", "none"):
        return False
    head = s[:10]
    return len(head) == 10 and head[4] == "-" and head[7] == "-"


def _reference_line_canonical(rd: dict) -> dict:
    """
    Formato v2 en BD: reference_date_id = fecha (FchRef), reference_code = folio (FolioRef).
    Filas legacy tenían esos dos campos intercambiados.
    """
    d = dict(rd) if rd else {}
    date_id = d.get("reference_date_id")
    code = d.get("reference_code")
    if _reference_value_is_date_like(code) and not _reference_value_is_date_like(date_id):
        d["reference_date_id"], d["reference_code"] = code, date_id
    return d


def _reference_line_v2_sii_fields(rd: dict) -> tuple[int, object, str, str | None]:
    """TpoDocRef, FolioRef, FchRef, RazonRef desde línea canónica v2."""
    c = _reference_line_canonical(rd)
    doc_type = _reference_doc_type_from_line_dict(c)
    folio_ref = _folio_ref_for_oc(c.get("reference_code"))
    ref_date = c.get("reference_date_id") or datetime.now().strftime("%Y-%m-%d")
    if str(ref_date).strip() in ("", "null", "None"):
        ref_date = datetime.now().strftime("%Y-%m-%d")
    ref_reason = c.get("reference_description")
    if ref_reason is None or str(ref_reason).strip() == "":
        ref_reason = "Orden de Compra" if doc_type == 801 else "Referencia"
    return doc_type, folio_ref, str(ref_date).strip()[:10], ref_reason


def _reference_doc_type_from_line_dict(rd):
    t = rd.get("reference_type_id")
    if t is not None and str(t).strip() not in ("", "null", "None"):
        try:
            return int(str(t).strip())
        except ValueError:
            pass
    return 801


class CustomerBillClass:
    def __init__(self, db: Session):
        self.db = db
        self.file_class = FileClass(db)  # Crear una instancia de FileClass

    @staticmethod
    def _bill_line_input_as_plain(item):
        """dict leíble para normalizar: soporta Request body dict, Pydantic BaseModel y otros objetos."""
        if isinstance(item, dict):
            return item
        model_dump = getattr(item, "model_dump", None)
        if callable(model_dump):
            try:
                return model_dump()
            except Exception:
                pass
        keys = (
            "quantity",
            "unit_amount",
            "amount",
            "description",
            "item_code",
            "item_name",
            "unit_measure",
            "discount_amount",
            "discount",
            "dsc_item",
        )
        return {k: getattr(item, k, None) for k in keys}

    def _clean_optional_str(self, item, *keys):
        for k in keys:
            if isinstance(item, dict):
                v = item.get(k)
            else:
                v = getattr(item, k, None)
            if v is None:
                continue
            s = str(v).strip()
            if s:
                return s
        return None

    def _optional_dsc_item_str(self, item):
        v = item.get("dsc_item") if isinstance(item, dict) else getattr(item, "dsc_item", None)
        if v is None:
            return None
        s = str(v).strip()
        return s[:500] if s else None

    def _discount_from_item_input(self, item):
        for k in ("discount_amount", "discount"):
            if isinstance(item, dict):
                v = item.get(k)
            else:
                v = getattr(item, k, None)
            if v is None or v == "":
                continue
            try:
                return max(0, int(v))
            except (TypeError, ValueError):
                return 0
        return 0

    def _normalize_bill_items(self, items):
        normalized = []
        if not items:
            return normalized

        for idx, item in enumerate(items, start=1):
            plain = self._bill_line_input_as_plain(item)
            quantity = plain.get("quantity")
            unit_amount = plain.get("unit_amount")
            amount = plain.get("amount")
            # Description field text only; code/name/unit live in their own columns.
            detail_only = (plain.get("description") or "").strip()

            try:
                q = int(quantity)
                u = int(unit_amount)
            except (TypeError, ValueError):
                continue

            name = self._clean_optional_str(plain, "item_name")
            code = self._clean_optional_str(plain, "item_code")
            if q < 1 or u < 0 or (not detail_only and not name and not code):
                continue

            try:
                total = int(amount) if amount is not None else q * u
            except (TypeError, ValueError):
                total = q * u

            if total <= 0:
                total = q * u

            da = self._discount_from_item_input(plain)
            stored_description = detail_only if detail_only else "-"
            dsc = self._optional_dsc_item_str(plain)
            if dsc is None and detail_only:
                dsc = detail_only
            if dsc is None and (name or code):
                dsc = name or code

            normalized.append({
                "line_number": idx,
                "quantity": q,
                "unit_amount": u,
                "total_amount": total,
                "description": stored_description,
                "item_code": code,
                "item_name": name,
                "unit_measure": self._clean_optional_str(plain, "unit_measure"),
                "discount_amount": da,
                "dsc_item": dsc if dsc else None,
            })
        return normalized

    def _replace_bill_items(self, dte_id: int, items):
        print("[_replace_bill_items] dte_id=", dte_id, "insertar", len(items), "fila(s)")
        self.db.query(CustomerDteItemModel).filter(CustomerDteItemModel.dte_id == dte_id).delete(
            synchronize_session=False
        )
        now = datetime.now()
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
                    added_date=now,
                    updated_date=now
                )
            )

    def _draft_dte_id_for_items(self, form_data, dte_row):
        """
        ID del borrador para leer customer_dte_items al emitir.
        Prioriza dte_row (resuelto por id o por _find_open_bill_draft) sobre form_data.id,
        para no mezclar borradores cuando el POST trae un id incorrecto.
        """
        if dte_row is not None and getattr(dte_row, "id", None) is not None:
            return int(dte_row.id)
        raw = getattr(form_data, "id", None)
        if raw is None:
            return None
        try:
            i = int(raw)
        except (TypeError, ValueError):
            return None
        return i if i != 0 else None

    def _get_bill_items_for_generation(self, form_data, dte_row):
        items = self._normalize_bill_items(getattr(form_data, "items", []))
        if items:
            return items
        dte_id = self._draft_dte_id_for_items(form_data, dte_row)
        if dte_id:
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

    def _collect_bill_reference_lines(self, form_data, dte_row):
        """Líneas si category_id=2: body del request o filas en dte_references (no hay resumen en dtes)."""
        lines = []
        refs = getattr(form_data, "references", None)
        if refs:
            for r in refs:
                d = _reference_line_to_dict(r)
                if _reference_line_nonempty(d):
                    lines.append(d)
            if lines:
                return lines
        if dte_row is not None and _bill_category_id(form_data, dte_row) == 2:
            q = (
                self.db.query(DteReferenceModel)
                .filter(DteReferenceModel.dte_id == dte_row.id)
                .order_by(DteReferenceModel.id)
                .all()
            )
            if q:
                for x in q:
                    lines.append(
                        {
                            "reference_type_id": x.reference_type_id,
                            "reference_date_id": x.reference_date_id,
                            "reference_code": x.reference_code,
                            "reference_description": x.reference_description,
                        }
                    )
                return lines
        return lines

    def _persist_dte_reference_rows(self, dte_id, reference_dicts):
        self.db.query(DteReferenceModel).filter(DteReferenceModel.dte_id == dte_id).delete()
        now = datetime.now()
        for rd in reference_dicts:
            if not _reference_line_nonempty(rd):
                continue
            row = DteReferenceModel(
                dte_id=dte_id,
                reference_type_id=rd.get("reference_type_id"),
                reference_date_id=rd.get("reference_date_id"),
                reference_code=rd.get("reference_code"),
                reference_description=rd.get("reference_description"),
                added_date=now,
            )
            self.db.add(row)

    def _bill_pre_emisor_receptor(self, customer_data, branch_office_data):
        """Bloques Emisor/Receptor comunes para pre_generate_bill (factura electrónica 33)."""
        return {
            "Emisor": {
                "RUTEmisor": "76063822-6",
                "CdgSIISucur": branch_office_data.dte_code,
            },
            "Receptor": {
                "RUTRecep": customer_data["customer_data"]["rut"],
                "RznSocRecep": customer_data["customer_data"]["customer"],
                "GiroRecep": customer_data["customer_data"]["activity"],
                "DirRecep": customer_data["customer_data"]["region"],
                "CmnaRecep": customer_data["customer_data"]["commune"],
                "Contacto": customer_data["customer_data"]["email"],
                "CorreoRecep": customer_data["customer_data"]["email"],
            },
        }

    def _bill_pre_detail_lines_parking_or_items(self, form_data, bill_items, qty):
        """
        Líneas Detalle para categorías 1 y 2: ítems persistidos/multilínea, chip+parking o una sola línea.
        """
        if bill_items:
            detail_lines = []
            for item in bill_items:
                line = libredte_detail_line_from_group_item(item)
                detail_lines.append(line)
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
            parking_qty = qty if qty is not None and qty >= 1 else 1
            parking_unit = round(parking / parking_qty) if parking_qty > 0 else parking
            return [
                {
                    "NmbItem": " Prestación de estacionamientos. Fecha:" + datetime.now().strftime("%d-%m-%Y"),
                    "QtyItem": parking_qty,
                    "PrcItem": parking_unit,
                },
                {
                    "NmbItem": "Chip",
                    "QtyItem": 1,
                    "PrcItem": DTE_CHIP_AMOUNT_CLP,
                },
            ]
        bill_qty = qty if qty is not None and qty >= 1 else 1
        bill_unit = round(int(form_data.amount) / bill_qty) if bill_qty > 0 else int(form_data.amount)
        return [
            {
                "NmbItem": " Prestación de estacionamientos. Fecha:" + datetime.now().strftime("%d-%m-%Y"),
                "QtyItem": bill_qty,
                "PrcItem": bill_unit,
            }
        ]

    def _find_open_bill_draft(self, form_data, dte_version_id=1):
        """
        Borrador factura 33 (folio 0, status 1/2) mismo criterio que generate() tras timbrar.
        Sirve para leer OC en pre_generate cuando el front no manda id (no masivo).
        """
        period_str = datetime.now().strftime("%Y-%m")
        expected_total = _bill_gross_for_dte_match(form_data)
        rut_clause = dte_rut_sql_or(DteModel.rut, form_data.rut)

        def _q(require_total: bool):
            q = (
                self.db.query(DteModel)
                .filter(
                    DteModel.branch_office_id == form_data.branch_office_id,
                    rut_clause,
                    DteModel.dte_type_id == 33,
                    DteModel.dte_version_id == dte_version_id,
                    DteModel.status_id.in_((1, 2)),
                    DteModel.period == period_str,
                    DteModel.folio == 0,
                )
            )
            if require_total:
                q = q.filter(DteModel.total == expected_total)
            return q.order_by(DteModel.id.desc()).first()

        dte = _q(True)
        if dte is None:
            dte = _q(False)
        if dte is None:
            dte = (
                self.db.query(DteModel)
                .filter(
                    DteModel.branch_office_id == form_data.branch_office_id,
                    rut_clause,
                    DteModel.dte_type_id == 33,
                    DteModel.dte_version_id == dte_version_id,
                    DteModel.status_id.in_((1, 2)),
                    DteModel.period == period_str,
                )
                .order_by(DteModel.id.desc())
                .first()
            )
        return dte

    def get_all(self, rol_id = None, rut = None, group = 1, page=0, items_per_page=10, dte_version_id=1):
        try:
            print(rol_id)
            if rol_id == 1 or rol_id == 2:
                # Inicialización de filtros dinámicos
                filters = []

                filters.append(DteModel.dte_version_id == dte_version_id)
                filters.append(DteModel.dte_type_id == 33)
                filters.append(DteModel.rut != None)

                if group == 1:
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

                    v2_folio_pool_ids = CustomerTicketClass(self.db)._v2_folio_pool_dte_ids(
                        [d.id for d in data]
                    )

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

                    v2_folio_pool_ids = CustomerTicketClass(self.db)._v2_folio_pool_dte_ids(
                        [d.id for d in data]
                    )

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
                        "status_id": dte.status_id,
                        "v2_emit": dte.id in v2_folio_pool_ids,
                    } for dte in data]

                    return serialized_data
            elif rol_id == 4:
                # Inicialización de filtros dinámicos
                filters = []

                filters.append(DteModel.dte_version_id == dte_version_id)
                filters.append(DteModel.dte_type_id == 33)
                filters.append(DteModel.rut != None)

                if group == 1:
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

                    v2_folio_pool_ids = CustomerTicketClass(self.db)._v2_folio_pool_dte_ids(
                        [d.id for d in data]
                    )

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

                    return serialized_data
            
        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
    
    def search(self, rol_id = None, supervisor_rut = None, branch_office_id=None, rut=None, customer=None, status_id=None, supervisor_id=None, page=0, items_per_page=10, category_id=None, dte_version_id=1):
        try:
            if rol_id == 1 or rol_id == 2:
                # Inicialización de filtros dinámicos
                filters = []

                if branch_office_id != None and branch_office_id != "":
                    filters.append(DteModel.branch_office_id == branch_office_id)
                if rut != None and rut != "" and rut != "":
                    filters.append(DteModel.rut == rut)
                if customer is not None and customer != "":
                    filters.append(CustomerModel.customer.like(f"%{customer}%"))
                if status_id != None and status_id != "":
                    filters.append(DteModel.status_id == status_id)
                if supervisor_id != None and supervisor_id != "":
                    filters.append(UserModel.supervisor_id == supervisor_id)
                if category_id is not None and category_id != "" and category_id != 0:
                    filters.append(DteModel.category_id == category_id)

                filters.append(DteModel.dte_version_id == dte_version_id)
                filters.append(DteModel.status_id < 4)
                filters.append(DteModel.dte_type_id == 33)
                filters.append(DteModel.rut != None)
                filters.append(DteModel.period == datetime.now().strftime('%Y-%m'))
                
                if supervisor_id != None:
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
                        UserModel, UserModel.rut == BranchOfficeModel.principal_supervisor
                    ).outerjoin(
                        CustomerModel, CustomerModel.rut == DteModel.rut
                    ).filter(
                        *filters
                    ).order_by(
                        desc(DteModel.folio)
                    )
                else:
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

                    v2_folio_pool_ids = CustomerTicketClass(self.db)._v2_folio_pool_dte_ids(
                        [d.id for d in data]
                    )

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

                    v2_folio_pool_ids = CustomerTicketClass(self.db)._v2_folio_pool_dte_ids(
                        [d.id for d in data]
                    )

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
                        "status_id": dte.status_id,
                        "v2_emit": dte.id in v2_folio_pool_ids,
                    } for dte in data]

                    return serialized_data
            elif rol_id == 4:
                # Inicialización de filtros dinámicos
                filters = []

                if branch_office_id != None:
                    filters.append(DteModel.branch_office_id == branch_office_id)
                if rut != None and rut != "":
                    filters.append(DteModel.rut == rut)
                if customer is not None:
                    filters.append(CustomerModel.customer.like(f"%{customer}%"))
                if status_id != None:
                    filters.append(DteModel.status_id == status_id)
                if supervisor_id != None:
                    filters.append(UserModel.supervisor_id == supervisor_id)
                if category_id is not None and category_id != "" and category_id != 0:
                    filters.append(DteModel.category_id == category_id)

                filters.append(DteModel.dte_version_id == dte_version_id)
                filters.append(DteModel.status_id < 4)
                filters.append(DteModel.dte_type_id == 33)
                filters.append(DteModel.rut != None)
                filters.append(DteModel.period == datetime.now().strftime('%Y-%m'))
                
                if supervisor_id != None:
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
                        UserModel, UserModel.rut == BranchOfficeModel.principal_supervisor
                    ).outerjoin(
                        CustomerModel, CustomerModel.rut == DteModel.rut
                    ).filter(
                        BranchOfficeModel.principal_supervisor == supervisor_rut
                    ).filter(
                        *filters
                    ).order_by(
                        desc(DteModel.folio)
                    )
                else:
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
                        BranchOfficeModel.principal_supervisor == supervisor_rut
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

                    v2_folio_pool_ids = CustomerTicketClass(self.db)._v2_folio_pool_dte_ids(
                        [d.id for d in data]
                    )

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

                    return serialized_data
        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
    
    def update(self, form_data):
        """
        Actualiza los datos de la patente en la base de datos.
        """
        dte = self.db.query(DteModel).filter(DteModel.id == form_data.id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        # Actualizar campos
        dte.branch_office_id = form_data.branch_office_id
        dte.rut = form_data.rut
        items = self._normalize_bill_items(getattr(form_data, "items", []))
        _apply_bill_draft_amounts(dte, form_data, pxq_items=items if items else None)
        dte.status_id = 2
        qty = getattr(form_data, "quantity", None)
        dte.quantity = int(qty) if qty is not None else None
        if items:
            dte.quantity = sum(i["quantity"] for i in items)

        refs = getattr(form_data, "references", None)
        if refs is not None:
            ref_dicts = []
            for r in refs:
                d = _reference_line_to_dict(r)
                if _reference_line_nonempty(d):
                    ref_dicts.append(d)
            if int(getattr(dte, "dte_version_id", 0) or 0) == DTE_VERSION_V2:
                ref_dicts = [_reference_line_canonical(d) for d in ref_dicts]
            self._persist_dte_reference_rows(dte.id, ref_dicts)

        if getattr(form_data, "items", None) is not None:
            self._replace_bill_items(dte.id, items)

        self.db.commit()
        self.db.refresh(dte)
    
    def change_status(self, form_data):
        """
        Actualiza los datos de la patente en la base de datos.
        """
        dte = self.db.query(DteModel).filter(DteModel.id == form_data.id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        # Actualizar campos
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

    def create_account_asset(self, form_data):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        if form_data.dte_type_id == 33:
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
                + "_Factura_"
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

    def reject(self, id):
        dte = self.db.query(DteModel).filter(DteModel.id == id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        dte.status_id = 3

        self.db.commit()
        self.db.refresh(dte)

    def _serialize_customer_dte_item_row(self, row):
        return {
            "line_number": row.line_number,
            "quantity": int(row.quantity),
            "unit_amount": int(row.unit_amount),
            "total_amount": int(row.total_amount),
            "description": (row.description or "").strip(),
            "item_code": (row.item_code or "").strip() or None,
            "item_name": (row.item_name or "").strip() or None,
            "unit_measure": (row.unit_measure or "").strip() or None,
            "discount_amount": int(getattr(row, "discount_amount", 0) or 0),
            "dsc_item": (getattr(row, "dsc_item", None) or "").strip() or None,
        }

    def list_customer_dte_items(self, dte_id: int):
        """Líneas de factura grupal desde customer_dte_items."""
        try:
            dte = self.db.query(DteModel.id).filter(DteModel.id == dte_id).first()
            if not dte:
                return {"status": "error", "message": "Dte no encontrado", "items": []}

            item_rows = (
                self.db.query(CustomerDteItemModel)
                .filter(CustomerDteItemModel.dte_id == dte_id)
                .order_by(CustomerDteItemModel.line_number.asc(), CustomerDteItemModel.id.asc())
                .all()
            )
            return {
                "status": "success",
                "dte_id": dte_id,
                "items": [self._serialize_customer_dte_item_row(r) for r in item_rows],
            }
        except Exception as e:
            return {"status": "error", "message": str(e), "items": []}
        
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
                DteModel.dte_version_id,
            ).outerjoin(BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id).outerjoin(
                CustomerModel, CustomerModel.rut == DteModel.rut
            ).filter(DteModel.id == id).first()

            if data_query:
                ref_rows = (
                    self.db.query(DteReferenceModel)
                    .filter(DteReferenceModel.dte_id == id)
                    .order_by(DteReferenceModel.id)
                    .all()
                )
                is_v2_bill = int(getattr(data_query, "dte_version_id", 0) or 0) == DTE_VERSION_V2
                # Serializar los datos del empleado
                customer_bill_data = {
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
                    "references": [
                        _reference_line_canonical(
                            {
                                "reference_type_id": x.reference_type_id,
                                "reference_date_id": x.reference_date_id,
                                "reference_code": x.reference_code,
                                "reference_description": x.reference_description,
                            }
                        )
                        if is_v2_bill
                        else {
                            "reference_type_id": x.reference_type_id,
                            "reference_date_id": x.reference_date_id,
                            "reference_code": x.reference_code,
                            "reference_description": x.reference_description,
                        }
                        for x in ref_rows
                    ],
                }

                items_payload = self.list_customer_dte_items(id)
                customer_bill_data["items"] = (
                    items_payload.get("items", [])
                    if isinstance(items_payload, dict)
                    else []
                )

                # Crear el resultado final como un diccionario
                result = {
                    "customer_bill_data": customer_bill_data
                }

                # Convierte el resultado a una cadena JSON
                serialized_result = json.dumps(result)

                return serialized_result

            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def save_pdf_bill(self, folio):
        folio = int(folio)
        tipo_dte = 33
        rut_emisor = '76063822'
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
        remote_path = f"{folio}.pdf"

        url = (
            f"https://libredte.cl/api/dte/dte_emitidos/pdf/{tipo_dte}/{folio}/{rut_emisor}"
            f"?formato=general&papelContinuo=0&copias_tributarias=1&copias_cedibles=1"
            f"&cedible=0&compress=0&base64=0"
        )

        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {TOKEN}'
        }

        response = requests.get(url, headers=headers, timeout=45)

        if response.status_code != 200 or not response.content:
            message = f"Error {response.status_code} al descargar PDF LibreDTE folio {folio}"
            print(message, response.text[:300] if response.text else "")
            return {"status": "error", "message": message}

        self.file_class.temporal_upload(response.content, remote_path)
        public_url = self.file_class.get(remote_path)
        print(f'PDF guardado en {public_url}', flush=True)
        return {"status": "success", "url": public_url}

    def generate(self, form_data):
        expected_total_doc = _bill_gross_for_dte_match(form_data)
        check_dte_existence = self.db.query(DteModel).filter(
            DteModel.branch_office_id == form_data.branch_office_id,
            DteModel.rut == form_data.rut,
            DteModel.total == expected_total_doc,
            DteModel.dte_type_id == 33,
            DteModel.dte_version_id == 1,
            DteModel.status_id == 4,
            DteModel.period == datetime.now().strftime('%Y-%m')
        ).count()

        if check_dte_existence == 0:
            customer = CustomerClass(self.db).get_by_rut(form_data.rut)
            customer_data = json.loads(customer)

            code = self.pre_generate_bill(customer_data, form_data)
            folio = None

            if code is not None:
                if isinstance(code, dict) and code.get("status") == "error":
                    return code
                if code == 402:
                    return "LibreDTE payment required"

                folio = self.generate_bill(customer_data['customer_data']['rut'], code)

                if folio is not None:
                    self.save_pdf_bill(folio)

            # store(): status_id=2 admin/supervisor, 1 cajero (rol 4)
            if folio is not None:
                dte = self._find_open_bill_draft(form_data)

                if dte:
                    dte.folio = folio
                    dte.status_id = 4
                    items = self._get_bill_items_for_generation(form_data, dte)
                    _sync_bill_dte_amounts_from_form(dte, form_data, pxq_items=items if items else None)
                    if items:
                        dte.quantity = sum(i["quantity"] for i in items)
                        self._replace_bill_items(dte.id, items)

                    try:
                        self.db.commit()
                        self.db.refresh(dte)

                        print("Empieza envio de whatsapp")
                        try:
                            WhatsappClass(self.db).send(dte, form_data.rut)
                        except Exception as we:
                            # El DTE ya quedó timbrado en LibreDTE; no revertir BD por fallo de WhatsApp o info/auxiliar.
                            print(f"WhatsApp/envío auxiliar falló (factura igual guardada): {we}")

                        return {"status": "success", "message": "Dte saved successfully"}
                    except Exception as e:
                        self.db.rollback()
                        return {"status": "error", "message": f"Error: {str(e)}"}
                else:
                    return {
                        "status": "error",
                        "message": "Dte not found after generation (no hay borrador tipo 33 o el total no coincide).",
                    }
            else:
                return {"status": "error", "message": "No se pudo obtener folio desde LibreDTE"}
        else:
            return {
                "status": "error",
                "message": "Ya existe un DTE para esta sucursal y este cliente.",
            }
            
    def store(self, form_data, rol_id, *, dte_version_id=1):
        if form_data.will_save == 1:
            raw_item_list = list(getattr(form_data, "items", None) or [])
            items = self._normalize_bill_items(raw_item_list)
            # Debug: consola del servidor (uvicorn/gunicorn) — si llegan items vacíos o se pierden al normalizar
            print("[customer_bills/store] category_id=", getattr(form_data, "category_id", None), end=" ")
            print("raw_len=", len(raw_item_list), "normalized_len=", len(items))
            try:
                for idx, raw in enumerate(raw_item_list):
                    plain = self._bill_line_input_as_plain(raw)
                    print(f"[customer_bills/store] raw[{idx}]=", json.dumps(plain, ensure_ascii=False, default=str))
                print("[customer_bills/store] normalized=", json.dumps(items, ensure_ascii=False, default=str))
            except Exception as dbg_e:
                print("[customer_bills/store] debug print error:", dbg_e)

            cid_pre = getattr(form_data, "category_id", None)
            if cid_pre is None:
                cid_pre = 1
            if cid_pre == 3:
                if len(raw_item_list) < 1:
                    return {
                        "status": "error",
                        "message": "Factura grupal requiere al menos un ítem en la lista de líneas.",
                    }
                if len(items) != len(raw_item_list) or not items:
                    return {
                        "status": "error",
                        "message": (
                            "No se guardaron todas las líneas: cada línea debe tener cantidad ≥ 1, precio unitario (neto) ≥ 1 "
                            "y al menos Detalle, Nombre o Código. Si esto aparece igual con el formulario bien llenado, revise que "
                            "**Factura grupal** esté en «Sí» antes de guardar."
                        ),
                    }

            dte = DteModel()

            period = datetime.now().strftime('%Y-%m')

            if rol_id == 1 or rol_id == 2:
                status_id = 2
            elif rol_id == 4:
                    status_id = 1
                    
            # Asignar los valores del formulario a la instancia del modelo
            dte.branch_office_id = form_data.branch_office_id
            dte.cashier_id = 0
            dte.dte_type_id = 33
            dte.dte_version_id = dte_version_id
            dte.status_id = status_id
            dte.rut = form_data.rut
            dte.folio = 0
            dte.card_amount = 0
            _apply_bill_draft_amounts(dte, form_data, pxq_items=items if items else None)
            dte.period = period
            dte.added_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            qty = getattr(form_data, "quantity", None)
            dte.quantity = int(qty) if qty is not None else None

            ref_dicts = []
            refs = getattr(form_data, "references", None)
            if refs:
                for r in refs:
                    d = _reference_line_to_dict(r)
                    if _reference_line_nonempty(d):
                        ref_dicts.append(d)

            self.db.add(dte)
            self.db.flush()

            if items:
                print("[customer_bills/store] guardando customer_dte_items dte.id=", dte.id, "filas=", len(items))
                dte.quantity = sum(i["quantity"] for i in items)
                self._replace_bill_items(dte.id, items)
            else:
                print("[customer_bills/store] NO se insertan líneas: items normalizado vacío (lista [])")

            if ref_dicts:
                if dte_version_id == DTE_VERSION_V2:
                    ref_dicts = [_reference_line_canonical(d) for d in ref_dicts]
                self._persist_dte_reference_rows(dte.id, ref_dicts)

            try:
                self.db.commit()
                return {"status": "success", "message": "Dte saved successfully"}
            except Exception as e:
                self.db.rollback()
                return {"status": "error", "message": f"Error: {str(e)}"}
        else:
            return {"status": "error", "message": "will_save debe ser 1 para guardar el DTE"}

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
            print(folio)

        if folio != None:
            dte.status_id = 5
            dte.reason_id = form_data.reason_id
            dte.comment = 'Código de autorización: Nota de Crédito ' + str(code)
            self.db.add(dte)
            self.db.commit()

            credit_note_dte = DteModel()
                    
            # Asignar los valores del formulario a la instancia del modelo
            credit_note_dte.branch_office_id = dte.branch_office_id
            credit_note_dte.cashier_id = 0
            credit_note_dte.dte_type_id = 61
            credit_note_dte.dte_version_id = 1
            credit_note_dte.status_id = 5
            credit_note_dte.chip_id = 0
            credit_note_dte.rut = customer_data['customer_data']['rut']
            credit_note_dte.folio = folio
            credit_note_dte.cash_amount = -abs(dte.cash_amount)
            credit_note_dte.card_amount = 0
            credit_note_dte.subtotal = -abs(round(dte.cash_amount/1.19))
            credit_note_dte.tax = -abs((dte.cash_amount) - round((dte.cash_amount)/1.19))
            credit_note_dte.discount = 0
            credit_note_dte.total = -abs(dte.cash_amount)
            credit_note_dte.period = datetime.now().strftime('%Y-%m')
            credit_note_dte.added_date = dte.added_date
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

    def store_credit_note_v2(self, form_data):
        return CustomerTicketClass(self.db).store_credit_note_v2(
            form_data,
            ref_dte_type=33,
            negative_amounts=True,
        )

    def pre_generate_bill(self, customer_data, form_data):  # Added self as the first argument
        branch_office_data = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == form_data.branch_office_id).first()

        dte_row = None
        _fid = getattr(form_data, "id", None)
        if _fid not in (None, 0):
            dte_row = self.db.query(DteModel).filter(DteModel.id == _fid).first()
        if dte_row is None:
            dte_row = self._find_open_bill_draft(form_data)

        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
        bill_items = self._get_bill_items_for_generation(form_data, dte_row)

        category_id = _bill_category_id(form_data, dte_row)
        if category_id not in (1, 2, 3):
            category_id = 1

        qty = getattr(form_data, "quantity", None)
        if qty is None and dte_row is not None and getattr(dte_row, "quantity", None) is not None:
            qty = dte_row.quantity
        qty = int(qty) if qty not in (None, "", 0) else None

        er = self._bill_pre_emisor_receptor(customer_data, branch_office_data)

        if category_id == 3:
            # Factura grupal: solo líneas de ítem (neto por línea, sin MntBruto).
            if not bill_items:
                return {
                    "status": "error",
                    "message": (
                        "Factura grupal (categoría 3) sin líneas de ítem: no hay ítems en el cuerpo del request "
                        "ni filas en customer_dte_items para el borrador. Revise el id del DTE o vuelva a guardar el borrador."
                    ),
                }
            detail_lines = []
            for item in bill_items:
                line = libredte_detail_line_from_group_item(item)
                detail_lines.append(line)
            if form_data.chip_id == 1:
                detail_lines.append(
                    {
                        "NmbItem": "Chip",
                        "QtyItem": 1,
                        "PrcItem": DTE_CHIP_AMOUNT_CLP,
                    }
                )
            data = {
                "Encabezado": {
                    "IdDoc": {"TipoDTE": 33},
                    **er,
                },
                "Detalle": detail_lines,
            }
        elif category_id == 2:
            # Con referencias (OC / otros): mismo detalle que flujo clásico, sin MntBruto; opcional Referencia.
            detail_lines = self._bill_pre_detail_lines_parking_or_items(form_data, bill_items, qty)
            data = {
                "Encabezado": {
                    "IdDoc": {"TipoDTE": 33},
                    **er,
                },
                "Detalle": detail_lines,
            }
            ref_lines = self._collect_bill_reference_lines(form_data, dte_row)
            if ref_lines:
                data["Referencia"] = []
                for i, rd in enumerate(ref_lines):
                    doc_type, folio_ref, ref_date, ref_reason = _reference_line_v2_sii_fields(rd)
                    data["Referencia"].append(
                        {
                            "NroLinRef": i + 1,
                            "TpoDocRef": doc_type,
                            "FolioRef": folio_ref,
                            "FchRef": ref_date,
                            "RazonRef": ref_reason,
                        }
                    )
        else:
            # category_id == 1: factura estándar (montos brutos en ítems vía MntBruto).
            detail_lines = self._bill_pre_detail_lines_parking_or_items(form_data, bill_items, qty)
            data = {
                "Encabezado": {
                    "IdDoc": {
                        "TipoDTE": 33,
                        "MntBruto": 1,
                    },
                    **er,
                },
                "Detalle": detail_lines,
            }

        try:
            # Payload exacto enviado a LibreDTE (POST json=data). Ver consola del backend al pre-generar.
            print("[pre_generate_bill] emitir payload:\n" + json.dumps(data, indent=2, ensure_ascii=False))
            # Endpoint para generar un DTE temporal
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
                if code is None:
                    return {
                        "status": "error",
                        "message": f"LibreDTE no devolvió código de autorización: {response.text}",
                    }
                return code
            else:
                return {
                    "status": "error",
                    "message": f"LibreDTE rechazó la emisión ({response.status_code}): {response.text}",
                }

        except Exception as e:
            print("Error al conectarse a la API:", e)
            return None

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
                    "TpoDocRef": 33,
                    "FolioRef": folio,
                    "FchRef": added_date,
                    "CodRef": 1,
                    "RazonRef": "Anula factura o boleta"
                }],
            }
        print(data)
        try:
            # Endpoint para generar un DTE temporal
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
            
            print(response.text)
            # Manejar la respuesta
            if response.status_code == 200:
                dte_data = response.json()
                print(dte_data)
                code = dte_data.get("codigo")

                return code
            else:
                return response.status_code

        except Exception as e:
            print("Error al conectarse a la API:", e)
            return None
    
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
    
    def get_dte_date(self, folio):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        # Endpoint para generar un DTE temporal
        url = f"https://libredte.cl/api/dte/dte_emitidos/info/33/" + str(folio) + '/76063822?getXML=0&getDetalle=0&getDatosDte=0&getTed=0&getResolucion=0&getEmailEnviados=0&getLinks=0&getReceptor=0&getSucursal=0&getUsuario=0'
            
        # Enviar solicitud a la API
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
            },
        )

        response_data = response.json()
        print(response_data)

        return response_data['fecha']
    
    def generate_bill(self, customer_rut, code):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        data = {
            "emisor": "76063822-6",
            "receptor": customer_rut,
            "dte": 33,
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
            if response.status_code == 200:
                dte_data = response.json()
                folio = dte_data.get("folio")

                return folio
            else:
                print("Error al generar el DTE:")
                print(response.status_code, response.json())
                return response.status_code

        except Exception as e:
            print("Error al conectarse a la API:", e)
            return None
        
    def download(self, id):
        dte = self.db.query(DteModel).filter(DteModel.id == id).first()

        if dte:
            TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

            # Endpoint para generar un DTE temporal
            url = f"https://libredte.cl/api/dte/dte_emitidos/pdf/33/"+ str(dte.folio) +"/76063822-6?formato=general&papelContinuo=0&copias_tributarias=1&copias_cedibles=1&cedible=0&compress=0&base64=0"

            # Enviar solicitud a la API
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )
            print(response.status_code)
            
            # Manejar la respuesta
            if response.status_code == 200:
                pdf_content = response.content
                timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                unique_id = uuid.uuid4().hex[:8]  # 8 caracteres únicos
                unique_filename = f"{timestamp}_{unique_id}.pdf"

                # Ruta remota en Azure
                remote_path = f"{unique_filename}"  # Organizar archivos en una carpeta específica

                self.file_class.temporal_upload(pdf_content, remote_path)  # Llamada correcta

                # Descargar archivo desde Azure File Share
                file_contents = self.file_class.download(remote_path)

                # Convertir el contenido del archivo a base64
                encoded_file = base64.b64encode(file_contents).decode('utf-8')

                self.file_class.delete(remote_path)  # Llamada correcta

                # Retornar el nombre del archivo y su contenido como base64
                return {
                    "file_name": unique_filename,
                    "file_data": encoded_file
                }
            else:
                return None
            
    def verify(self, id):
        """
        Actualiza los datos de la patente en la base de datos.
        """
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
        dtes = self.db.query(DteModel).filter(DteModel.status_id == 4).filter(DteModel.dte_type_id  == 33).filter(DteModel.dte_version_id == 1).all()

        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        for dte in dtes:
            print(f"Verificando DTE tipo 33 folio: {dte.folio}")

            url = f"https://libredte.cl/api/dte/dte_emitidos/cobro/33/{dte.folio}/76063822?getDocumento=0&getDetalle=0&getLinks=0"
                
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

    def get_all_v2(self, rol_id=None, rut=None, group=1, page=0, items_per_page=10):
        return self.get_all(rol_id, rut, group, page, items_per_page, dte_version_id=DTE_VERSION_V2)

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
        )

    def store_v2(self, form_data, rol_id):
        return self.store(form_data, rol_id, dte_version_id=DTE_VERSION_V2)

    def _v2_format_bill_detail_lines(self, detail_lines, category_id: int) -> tuple[list, int, int, int]:
        """Detalle invoiceV2 factura 33. Cat. 2/3: precios netos; cat. 1: brutos (MntBruto)."""
        prices_are_net = int(category_id or 1) in (2, 3)
        formatted: list[dict] = []
        for index, line in enumerate(detail_lines, start=1):
            qty = int(line.get("QtyItem", 1) or 1)
            prc_raw = int(line.get("PrcItem", 0) or 0)
            monto_raw = line.get("MontoItem")
            if prices_are_net:
                line_net = int(monto_raw) if monto_raw is not None else qty * prc_raw
                unit_net = prc_raw if qty <= 1 else max(0, round(line_net / qty))
            else:
                line_gross = int(monto_raw) if monto_raw is not None else qty * prc_raw
                line_net = round(line_gross / 1.19)
                unit_net = round(prc_raw / 1.19) if prc_raw else 0
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
            formatted.append(entry)
        net_amount = sum(int(e["MontoItem"]) for e in formatted)
        tax_amount = round(net_amount * 0.19)
        total_amount = net_amount + tax_amount
        return formatted, net_amount, tax_amount, total_amount

    def _bill_v2_detail_lines(self, form_data, dte_row, bill_items, category_id, qty):
        """Misma lógica de líneas que pre_generate_bill (LibreDTE) para armar Detalle v2."""
        if category_id == 3:
            if not bill_items:
                return {
                    "status": "error",
                    "message": (
                        "Factura grupal (categoría 3) sin líneas de ítem: cargue ítems o guarde el borrador."
                    ),
                }
            detail_lines = [libredte_detail_line_from_group_item(item) for item in bill_items]
            if form_data.chip_id == 1:
                detail_lines.append({"NmbItem": "Chip", "QtyItem": 1, "PrcItem": DTE_CHIP_AMOUNT_CLP})
            return detail_lines
        return self._bill_pre_detail_lines_parking_or_items(form_data, bill_items, qty)

    def _build_bill_document_v2(
        self,
        customer,
        form_data,
        detail_lines,
        branch,
        *,
        folio: int,
        category_id: int,
        dte_row=None,
    ):
        issue_date = v2_dte_api_date()
        due_date = v2_dte_api_date(datetime.now() + timedelta(days=30))
        formatted_lines, net_amount, tax_amount, total_amount = self._v2_format_bill_detail_lines(
            detail_lines, category_id
        )

        issuer = ticket_v2_issuer(branch)
        receiver = {
            "RUTRecep": customer["rut"],
            "RznSocRecep": customer.get("customer") or customer["rut"],
        }
        if customer.get("activity"):
            receiver["GiroRecep"] = customer["activity"]
        if customer.get("address") or customer.get("region"):
            receiver["DirRecep"] = customer.get("address") or customer.get("region")
        if customer.get("commune"):
            receiver["CmnaRecep"] = customer["commune"]
        # No CorreoRecep/Contacto en invoiceV2 (correo solo vía DteSubscriberEmailClass).

        id_doc: dict = {
            "TipoDTE": 33,
            "FchEmis": issue_date,
            "FchVenc": due_date,
            "Folio": int(folio),
        }
        if int(category_id or 1) == 1:
            id_doc["MntBruto"] = 1

        document: dict = {
            "Encabezado": {
                "IdDoc": id_doc,
                "Emisor": issuer,
                "Receptor": receiver,
                "Totales": {
                    "MntNeto": net_amount,
                    "IVA": tax_amount,
                    "MntTotal": total_amount,
                },
            },
            "Detalle": formatted_lines,
        }

        ref_lines = self._collect_bill_reference_lines(form_data, dte_row)
        if ref_lines and int(category_id or 1) == 2:
            document["Referencia"] = []
            for i, rd in enumerate(ref_lines):
                doc_type, folio_ref, ref_date, ref_reason = _reference_line_v2_sii_fields(rd)
                document["Referencia"].append(
                    {
                        "NroLinRef": i + 1,
                        "TpoDocRef": doc_type,
                        "FolioRef": folio_ref,
                        "FchRef": ref_date,
                        "RazonRef": ref_reason,
                    }
                )
        return document

    def test_emit_bill_v2(self, form_data):
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
        customer_record = customer_data["customer_data"]

        qty = getattr(form_data, "quantity", None)
        qty = int(qty) if qty not in (None, "", 0) else None
        detail_lines = self._bill_pre_detail_lines_parking_or_items(form_data, [], qty)
        document = self._build_bill_document_v2(
            customer_record,
            form_data,
            detail_lines,
            branch,
            folio=999999,
            category_id=int(getattr(form_data, "category_id", None) or 1),
            dte_row=None,
        )
        return CustomerTicketClass(self.db).emit_invoice_v2(document, branch, "Factura")

    def generate_v2(self, form_data):
        expected_total_doc = _bill_gross_for_dte_match(form_data)
        check_dte_existence = (
            self.db.query(DteModel)
            .filter(
                DteModel.branch_office_id == form_data.branch_office_id,
                DteModel.rut == form_data.rut,
                DteModel.total == expected_total_doc,
                DteModel.dte_type_id == 33,
                DteModel.dte_version_id == DTE_VERSION_V2,
                DteModel.status_id == 4,
                DteModel.period == datetime.now().strftime("%Y-%m"),
            )
            .count()
        )
        if check_dte_existence != 0:
            return {
                "status": "error",
                "message": "Ya existe un DTE para esta sucursal y este cliente.",
            }

        customer = CustomerClass(self.db).get_by_rut(form_data.rut)
        customer_data = json.loads(customer)
        if "customer_data" not in customer_data:
            return {"status": "error", "message": "Cliente no encontrado"}
        customer_record = customer_data["customer_data"]

        branch = (
            self.db.query(BranchOfficeModel)
            .filter(BranchOfficeModel.id == form_data.branch_office_id)
            .first()
        )
        if not branch:
            return {"status": "error", "message": "Sucursal no encontrada"}

        dte_row = None
        if getattr(form_data, "id", None):
            dte_row = (
                self.db.query(DteModel)
                .filter(
                    DteModel.id == form_data.id,
                    DteModel.dte_type_id == 33,
                    DteModel.dte_version_id == DTE_VERSION_V2,
                    DteModel.status_id.in_((1, 2)),
                    DteModel.folio == 0,
                )
                .first()
            )
        if not dte_row:
            dte_row = self._find_open_bill_draft(form_data, dte_version_id=DTE_VERSION_V2)
        if not dte_row:
            return {
                "status": "error",
                "message": "No hay borrador v2 en dtes para emitir (status 1 o 2, folio 0).",
            }

        folio_res = FolioClass(self.db).reserve_next_by_document_type(
            33,
            branch_office_id=getattr(form_data, "branch_office_id", None),
            dte_id=dte_row.id,
        )
        if folio_res.get("status") != "success":
            return folio_res

        bill_items = self._get_bill_items_for_generation(form_data, dte_row)
        category_id = _bill_category_id(form_data, dte_row)
        qty = getattr(form_data, "quantity", None)
        if qty is None and dte_row is not None and getattr(dte_row, "quantity", None) is not None:
            qty = dte_row.quantity
        qty = int(qty) if qty not in (None, "", 0) else None

        detail_lines = self._bill_v2_detail_lines(form_data, dte_row, bill_items, category_id, qty)
        if isinstance(detail_lines, dict) and detail_lines.get("status") == "error":
            FolioClass(self.db).release_folio_pool(folio_res["id"])
            return detail_lines

        document = self._build_bill_document_v2(
            customer_record,
            form_data,
            detail_lines,
            branch,
            folio=int(folio_res["folio"]),
            category_id=category_id,
            dte_row=dte_row,
        )
        emit_result = CustomerTicketClass(self.db).emit_invoice_v2(document, branch, "Factura")

        if emit_result.get("status") != "success":
            FolioClass(self.db).release_folio_pool(folio_res["id"])
            return {
                "status": "error",
                "message": emit_result.get("message") or "Emisión v2 no emitió la factura",
                "errors": emit_result.get("errors"),
                "response": emit_result.get("response"),
            }

        folio_number = int(folio_res["folio"])

        dte_row.folio = folio_number
        dte_row.status_id = 4
        dte_row.dte_version_id = DTE_VERSION_V2
        dte_row.updated_date = datetime.now()
        items = self._get_bill_items_for_generation(form_data, dte_row)
        mnt_total = int(
            (document.get("Encabezado") or {}).get("Totales", {}).get("MntTotal") or 0
        )
        if mnt_total > 0:
            cid = int(category_id or 1)
            chip = int(getattr(form_data, "chip_id", 0) or 0)
            if cid == 3:
                chip = 0
            dte_row.chip_id = chip
            dte_row.category_id = cid
            _set_dte_gross_totals(dte_row, mnt_total)
        else:
            _sync_bill_dte_amounts_from_form(dte_row, form_data, pxq_items=items if items else None)
        if items:
            dte_row.quantity = sum(i["quantity"] for i in items)
            self._replace_bill_items(dte_row.id, items)

        try:
            self.db.commit()
            self.db.refresh(dte_row)
            FolioClass(self.db).bind_folio_to_dte(folio_res["id"], dte_row.id)
            from app.backend.classes.dte_subscriber_email_class import DteSubscriberEmailClass

            recipient_email = (customer_record.get("email") or "").strip()
            customer_obj = (
                self.db.query(CustomerModel)
                .filter(CustomerModel.rut == form_data.rut)
                .first()
            )
            email_result = DteSubscriberEmailClass(self.db).send(
                dte_row,
                customer=customer_obj,
                to_emails=recipient_email,
            )

            print("Empieza envio de whatsapp v2 (payments)", flush=True)
            whatsapp_result = WhatsappClass(self.db).send_v2_invoice(dte_row, form_data.rut)
            print(f"[v2] whatsapp_result folio={dte_row.folio}: {whatsapp_result}", flush=True)

            return {
                "status": "success",
                "message": "Dte saved successfully",
                "folio": folio_number,
                "response": emit_result.get("response"),
                "email": email_result,
                "whatsapp": whatsapp_result,
            }
        except Exception as e:
            self.db.rollback()
            FolioClass(self.db).release_folio_pool(folio_res["id"])
            return {"status": "error", "message": f"Error: {str(e)}"}


