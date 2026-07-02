from __future__ import annotations

import json
import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.backend.classes.payment_gateway_class import PaymentGatewayClass
from app.backend.db.models import (
    BranchOfficeModel,
    CustomerModel,
    DteModel,
    DtePaymentDataModel,
)

# Same ids used on dtes.payment_type_id (2 = card / online gateway)
PAYMENT_TYPE_LABELS: dict[int, str] = {
    1: "Efectivo",
    2: "Tarjeta",
    3: "Transferencia",
}


def document_folio_from_reference_id(reference_id: str | None) -> int | None:
    """Parse document folio from reference_id (numeric, 32130049-r2, legacy intrajis-dte-*)."""
    if not reference_id:
        return None
    ref = str(reference_id).strip()
    if ref.isdigit():
        return int(ref)
    prefix = re.match(r"^(\d+)", ref)
    if prefix:
        return int(prefix.group(1))
    match = re.search(r"(?:intrajis-dte-\d+-)?(\d+)$", ref, re.I)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def payment_type_id_from_gateway(gateway_response: dict | None, payment_status: str | None) -> int | None:
    """Map gateway response to internal payment_type_id."""
    if payment_status != "completed":
        return None
    method = None
    if isinstance(gateway_response, dict):
        selected = gateway_response.get("selected_method")
        if isinstance(selected, dict):
            method = (selected.get("type") or selected.get("name") or "").lower()
        elif isinstance(selected, str):
            method = selected.lower()
        methods = gateway_response.get("methods")
        if not method and isinstance(methods, list) and methods:
            method = str(methods[0]).lower()
    if method and any(k in method for k in ("transfer", "transferencia")):
        return 3
    return 2


class DtePaymentDataClass:
    def __init__(self, db: Session):
        self.db = db

    def record_order_created(
        self,
        *,
        dte,
        customer,
        order_id: str,
        reference_id: str,
        gateway_response: dict | None = None,
    ) -> dict:
        """Persist a newly created gateway order so folio pay links can retry without a new WhatsApp."""
        order_id = (order_id or "").strip()
        reference_id = (reference_id or "").strip()
        if not order_id or not reference_id:
            return {"status": "error", "message": "order_id and reference_id are required"}

        existing = (
            self.db.query(DtePaymentDataModel)
            .filter(DtePaymentDataModel.order_id == order_id)
            .first()
        )
        if existing:
            return {"status": "success", "payment_data": self.serialize(existing)}

        document_folio = document_folio_from_reference_id(reference_id)
        if document_folio is None and dte and getattr(dte, "folio", None):
            document_folio = int(dte.folio)
        amount = int(getattr(dte, "total", 0) or 0) if dte else None
        now = datetime.now()
        raw_json = json.dumps(
            {"source": "order_created", "gateway": gateway_response or {}},
            ensure_ascii=False,
            default=str,
        )
        row = DtePaymentDataModel(
            dte_id=dte.id if dte else None,
            customer_id=customer.id if customer else None,
            branch_office_id=getattr(dte, "branch_office_id", None) if dte else None,
            folio=document_folio,
            reference_id=reference_id,
            order_id=order_id,
            payment_status="pending",
            amount=amount,
            rut=getattr(dte, "rut", None) if dte else None,
            raw_payload=raw_json,
            added_date=now,
            updated_date=now,
        )
        self.db.add(row)
        try:
            self.db.commit()
            self.db.refresh(row)
        except Exception as exc:
            self.db.rollback()
            return {"status": "error", "message": f"Failed to save payment order: {exc}"}
        return {"status": "success", "payment_data": self.serialize(row)}

    def _find_dte(self, document_folio: int | None, reference_id: str) -> DteModel | None:
        if document_folio:
            row = (
                self.db.query(DteModel)
                .filter(DteModel.folio == document_folio)
                .order_by(DteModel.id.desc())
                .first()
            )
            if row:
                return row
        legacy_match = re.match(r"intrajis-dte-(\d+)-", reference_id or "", re.I)
        if legacy_match:
            try:
                dte_id = int(legacy_match.group(1))
                return self.db.query(DteModel).filter(DteModel.id == dte_id).first()
            except ValueError:
                pass
        return None

    def _resolve_customer(self, dte: DteModel | None) -> CustomerModel | None:
        if not dte or not dte.rut:
            return None
        return (
            self.db.query(CustomerModel)
            .filter(CustomerModel.rut == dte.rut)
            .first()
        )

    def record_payment_return(
        self,
        reference_id: str,
        order_id: str,
        *,
        source: str = "return_url",
    ) -> dict:
        reference_id = (reference_id or "").strip()
        order_id = (order_id or "").strip()
        if not reference_id or not order_id:
            return {"status": "error", "message": "referenceId and orderId are required"}

        document_folio = document_folio_from_reference_id(reference_id)
        dte = self._find_dte(document_folio, reference_id)
        customer = self._resolve_customer(dte)

        gateway_response: dict = {}
        payment_status = None
        amount = None
        try:
            gateway_response = PaymentGatewayClass().get_order(order_id) or {}
            if isinstance(gateway_response, dict):
                payment_status = gateway_response.get("status")
                amount_block = gateway_response.get("amount") or {}
                if isinstance(amount_block, dict) and amount_block.get("total") is not None:
                    amount = int(float(amount_block["total"]))
        except Exception as exc:
            gateway_response = {"fetch_error": str(exc)}

        rut = getattr(dte, "rut", None) if dte else None
        customer_id = customer.id if customer else None
        branch_office_id = getattr(dte, "branch_office_id", None) if dte else None
        payment_type_id = payment_type_id_from_gateway(gateway_response, payment_status)

        if amount is None and dte and getattr(dte, "total", None):
            amount = int(dte.total)
        if document_folio is None and dte and getattr(dte, "folio", None):
            document_folio = int(dte.folio)

        now = datetime.now()
        row = (
            self.db.query(DtePaymentDataModel)
            .filter(DtePaymentDataModel.order_id == order_id)
            .first()
        )
        raw_json = json.dumps(
            {"source": source, "gateway": gateway_response},
            ensure_ascii=False,
            default=str,
        )

        if row:
            row.reference_id = reference_id
            row.dte_id = dte.id if dte else row.dte_id
            row.customer_id = customer_id or row.customer_id
            row.payment_type_id = payment_type_id or row.payment_type_id
            row.branch_office_id = branch_office_id or row.branch_office_id
            row.folio = document_folio or row.folio
            row.payment_status = payment_status or row.payment_status
            row.amount = amount if amount is not None else row.amount
            row.rut = rut or row.rut
            row.raw_payload = raw_json
            row.updated_date = now
        else:
            row = DtePaymentDataModel(
                dte_id=dte.id if dte else None,
                customer_id=customer_id,
                payment_type_id=payment_type_id,
                branch_office_id=branch_office_id,
                folio=document_folio,
                reference_id=reference_id,
                order_id=order_id,
                payment_status=payment_status,
                amount=amount,
                rut=rut,
                raw_payload=raw_json,
                added_date=now,
                updated_date=now,
            )
            self.db.add(row)

        dte_updated = False
        if dte and payment_status == "completed" and dte.status_id == 4:
            resolved_payment_type_id = payment_type_id or 2
            dte.status_id = 5
            dte.payment_type_id = resolved_payment_type_id
            if resolved_payment_type_id == 2:
                # Klap tarjeta: el monto imputado pasa de cash_amount → card_amount
                paid_amount = int(dte.cash_amount or 0) or int(amount or 0) or int(dte.total or 0)
                dte.card_amount = paid_amount
                dte.cash_amount = 0
            else:
                dte.card_amount = amount or dte.total
            dte.payment_date = now.strftime("%Y-%m-%d")
            dte.updated_date = now
            dte_updated = True

        try:
            self.db.commit()
            self.db.refresh(row)
        except Exception as exc:
            self.db.rollback()
            return {"status": "error", "message": f"Failed to save payment data: {exc}"}

        if dte_updated and dte and getattr(dte, "folio", None):
            try:
                from app.backend.classes.whatsapp_class import WhatsappClass

                WhatsappClass(self.db).notify_payment(dte.folio)
            except Exception as exc:
                print(f"[payments] notify_payment folio={dte.folio}: {exc}", flush=True)

        return {
            "status": "success",
            "payment_data": self.serialize(row),
            "dte_updated": dte_updated,
        }

    def get_by_order_id(self, order_id: str) -> dict | None:
        row = (
            self.db.query(DtePaymentDataModel)
            .filter(DtePaymentDataModel.order_id == order_id)
            .first()
        )
        if not row:
            return None
        return self.serialize(row)

    def serialize(self, row: DtePaymentDataModel) -> dict:
        customer_name = None
        if row.customer_id:
            customer = (
                self.db.query(CustomerModel)
                .filter(CustomerModel.id == row.customer_id)
                .first()
            )
            if customer:
                customer_name = customer.customer

        branch_office_name = None
        if row.branch_office_id:
            branch = (
                self.db.query(BranchOfficeModel)
                .filter(BranchOfficeModel.id == row.branch_office_id)
                .first()
            )
            if branch:
                branch_office_name = branch.branch_office

        payment_type_label = None
        if row.payment_type_id is not None:
            payment_type_label = PAYMENT_TYPE_LABELS.get(
                int(row.payment_type_id),
                f"Tipo {row.payment_type_id}",
            )

        return {
            "id": row.id,
            "dte_id": row.dte_id,
            "customer_id": row.customer_id,
            "payment_type_id": row.payment_type_id,
            "branch_office_id": row.branch_office_id,
            "document_folio": row.folio,
            "reference_id": row.reference_id,
            "order_id": row.order_id,
            "payment_status": row.payment_status,
            "amount": row.amount,
            "rut": row.rut,
            "customer_name": customer_name,
            "branch_office": branch_office_name,
            "payment_type": payment_type_label,
            "added_date": row.added_date.strftime("%d-%m-%Y")
            if row.added_date
            else None,
        }
