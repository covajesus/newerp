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


def document_folio_from_reference_id(reference_id: str | None) -> int | None:
    """Parse document folio from reference_id (numeric or legacy intrajis-dte-{id}-{folio})."""
    if not reference_id:
        return None
    ref = str(reference_id).strip()
    if ref.isdigit():
        return int(ref)
    match = re.search(r"(?:intrajis-dte-\d+-)?(\d+)$", ref, re.I)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


class DtePaymentDataClass:
    def __init__(self, db: Session):
        self.db = db

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

        gateway_response: dict = {}
        payment_status = None
        amount = None
        payment_method = None
        try:
            gateway_response = PaymentGatewayClass().get_order(order_id) or {}
            if isinstance(gateway_response, dict):
                payment_status = gateway_response.get("status")
                amount_block = gateway_response.get("amount") or {}
                if isinstance(amount_block, dict) and amount_block.get("total") is not None:
                    amount = int(float(amount_block["total"]))
                payment_method = gateway_response.get("selected_method")
                if isinstance(payment_method, dict):
                    payment_method = payment_method.get("name") or payment_method.get("type")
        except Exception as exc:
            gateway_response = {"fetch_error": str(exc)}

        rut = getattr(dte, "rut", None) if dte else None
        customer_name = None
        branch_name = None
        if dte and dte.rut:
            customer = (
                self.db.query(CustomerModel)
                .filter(CustomerModel.rut == dte.rut)
                .first()
            )
            if customer:
                customer_name = getattr(customer, "customer", None)
        if dte and dte.branch_office_id:
            branch = (
                self.db.query(BranchOfficeModel)
                .filter(BranchOfficeModel.id == dte.branch_office_id)
                .first()
            )
            if branch:
                branch_name = getattr(branch, "branch_office", None)

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
            row.folio = document_folio or row.folio
            row.payment_status = payment_status or row.payment_status
            row.amount = amount if amount is not None else row.amount
            row.rut = rut or row.rut
            row.customer_name = customer_name or row.customer_name
            row.branch_office = branch_name or row.branch_office
            row.payment_method = payment_method or row.payment_method
            row.raw_payload = raw_json
            row.updated_date = now
        else:
            row = DtePaymentDataModel(
                dte_id=dte.id if dte else None,
                folio=document_folio,
                reference_id=reference_id,
                order_id=order_id,
                payment_status=payment_status,
                amount=amount,
                rut=rut,
                customer_name=customer_name,
                branch_office=branch_name,
                payment_method=payment_method,
                raw_payload=raw_json,
                added_date=now,
                updated_date=now,
            )
            self.db.add(row)

        dte_updated = False
        if dte and payment_status == "completed" and dte.status_id == 4:
            dte.status_id = 5
            dte.payment_type_id = 2
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
        return {
            "id": row.id,
            "dte_id": row.dte_id,
            "document_folio": row.folio,
            "reference_id": row.reference_id,
            "order_id": row.order_id,
            "payment_status": row.payment_status,
            "amount": row.amount,
            "rut": row.rut,
            "customer_name": row.customer_name,
            "branch_office": row.branch_office,
            "payment_method": row.payment_method,
            "added_date": row.added_date.strftime("%d-%m-%Y %H:%M")
            if row.added_date
            else None,
        }
