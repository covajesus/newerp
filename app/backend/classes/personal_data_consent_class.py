"""Guarda la aceptacion del aviso de datos personales como un formulario."""

from __future__ import annotations

import json
from datetime import datetime
from urllib.parse import unquote

import pytz
from fastapi import Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.backend.classes.payment_gateway_class import normalize_gateway_order_id
from app.backend.db.models import (
    BranchOfficeModel,
    CustomerModel,
    DteModel,
    DtePaymentDataModel,
    PersonalDataConsentModel,
)

_TZ = pytz.timezone("America/Santiago")
_WEEKDAYS = (
    "lunes",
    "martes",
    "miercoles",
    "jueves",
    "viernes",
    "sabado",
    "domingo",
)
_DTE_TYPES = {
    33: "Factura",
    34: "Factura exenta",
    39: "Boleta",
    41: "Boleta exenta",
    52: "Guia de despacho",
    56: "Nota de debito",
    61: "Nota de credito",
}
CONSENT_TITLE = "Tratamiento de datos personales (Ley N° 21.719)"
CONSENT_BODY = (
    "JIS Parking tratara sus datos personales esenciales —nombre, RUT, telefono, "
    "correo electronico, descripcion del caso, fecha/lugar del suceso y adjuntos— "
    "para registrar, gestionar y responder su sugerencia, reclamo o felicitacion, "
    "y para darle seguimiento por correo, WhatsApp o el portal de seguimiento. "
    "La base legal es su consentimiento previo, libre, especifico e inequivoco. "
    "No usaremos estos datos para marketing. Puede ejercer sus derechos de acceso, "
    "rectificacion, supresion, oposicion, portabilidad y bloqueo, y revocar este "
    "consentimiento en cualquier momento, escribiendo a contacto@jisparking.com "
    "o en nuestra Politica de Privacidad."
)
CONSENT_STATEMENT = (
    "He leido la informacion anterior y autorizo el tratamiento de mis datos "
    "personales para las finalidades indicadas."
)
LEGAL_BASIS = "Consentimiento previo, libre, especifico e inequivoco"


class PersonalDataConsentClass:
    def __init__(self, db: Session):
        self.db = db

    def already_accepted(self, pay_id: str) -> bool:
        """True si este cliente (o este mismo enlace) ya dejo el consentimiento."""
        cleaned = _clean_pay_id(pay_id)
        dte = self._resolve_dte(cleaned)
        clauses = []
        rut = str(dte.rut).strip() if dte and dte.rut else ""
        if rut:
            clauses.append(PersonalDataConsentModel.rut == rut)
        if cleaned:
            clauses.append(PersonalDataConsentModel.pay_id == cleaned)
        if dte and dte.folio is not None:
            clauses.append(PersonalDataConsentModel.folio == int(dte.folio))
        if not clauses:
            return False
        row = (
            self.db.query(PersonalDataConsentModel.id)
            .filter(PersonalDataConsentModel.accepted == 1)
            .filter(or_(*clauses))
            .first()
        )
        return row is not None

    def record_acceptance(self, pay_id: str, request: Request | None = None) -> PersonalDataConsentModel:
        cleaned = _clean_pay_id(pay_id)
        dte = self._resolve_dte(cleaned)
        customer = None
        if dte and dte.rut:
            customer = (
                self.db.query(CustomerModel)
                .filter(CustomerModel.rut == dte.rut)
                .first()
            )
        branch = None
        if dte and dte.branch_office_id:
            branch = (
                self.db.query(BranchOfficeModel)
                .filter(BranchOfficeModel.id == dte.branch_office_id)
                .first()
            )

        now = datetime.now(_TZ).replace(tzinfo=None)
        document_type = _DTE_TYPES.get(int(dte.dte_type_id or 0), None) if dte else None
        branch_name = getattr(branch, "branch_office", None) if branch else None
        amount = None
        if dte is not None:
            from app.backend.classes.customer_ticket_class import ticket_payment_total

            amount = ticket_payment_total(dte)

        folio = int(dte.folio) if dte and dte.folio is not None else None
        case_description = (
            f"Aceptacion para continuar al pago de {document_type or 'documento'}"
            + (f" folio {folio}" if folio else "")
            + (f" por ${amount}" if amount is not None else "")
            + "."
        )
        form = {
            "acepta": True,
            "nombre": getattr(customer, "customer", None) if customer else None,
            "rut": (dte.rut if dte and dte.rut else None) or (getattr(customer, "rut", None) if customer else None),
            "telefono": getattr(customer, "phone", None) if customer else None,
            "correo": getattr(customer, "email", None) if customer else None,
            "descripcion_del_caso": case_description,
            "fecha_del_documento": dte.added_date.strftime("%Y-%m-%d %H:%M:%S") if dte and dte.added_date else None,
            "lugar": branch_name,
            "adjuntos": "Sin adjuntos",
            "folio": folio,
            "tipo_documento": document_type,
            "monto": amount,
            "pay_id": cleaned,
            "dia": _WEEKDAYS[now.weekday()],
            "fecha": now.strftime("%Y-%m-%d"),
            "hora": now.strftime("%H:%M:%S"),
            "declaracion": CONSENT_STATEMENT,
        }

        row = PersonalDataConsentModel(
            accepted=1,
            rut=form["rut"],
            customer_name=form["nombre"],
            email=form["correo"],
            phone=form["telefono"],
            customer_id=getattr(customer, "id", None) if customer else None,
            dte_id=getattr(dte, "id", None) if dte else None,
            folio=folio,
            dte_type_id=getattr(dte, "dte_type_id", None) if dte else None,
            document_type=document_type,
            branch_office_id=getattr(dte, "branch_office_id", None) if dte else None,
            branch_office_name=branch_name,
            amount=amount,
            pay_id=cleaned or None,
            case_description=case_description,
            event_place=branch_name,
            document_datetime=getattr(dte, "added_date", None) if dte else None,
            attachments_note="Sin adjuntos",
            consent_title=CONSENT_TITLE,
            consent_body=CONSENT_BODY,
            consent_statement=CONSENT_STATEMENT,
            legal_basis=LEGAL_BASIS,
            form_json=json.dumps(form, ensure_ascii=False),
            ip_address=_client_ip(request),
            user_agent=_user_agent(request),
            accepted_datetime=now,
            accepted_date=now.date(),
            accepted_time=now.strftime("%H:%M:%S"),
            year=now.year,
            month=now.month,
            day=now.day,
            hour=now.hour,
            minute=now.minute,
            second=now.second,
            weekday=now.weekday(),
            weekday_name=_WEEKDAYS[now.weekday()],
            added_date=now,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def _resolve_dte(self, pay_id: str) -> DteModel | None:
        if not pay_id:
            return None
        if pay_id.isdigit():
            return (
                self.db.query(DteModel)
                .filter(DteModel.folio == int(pay_id))
                .order_by(DteModel.id.desc())
                .first()
            )
        normalized = normalize_gateway_order_id(pay_id)
        payment = (
            self.db.query(DtePaymentDataModel)
            .filter(DtePaymentDataModel.order_id == normalized)
            .order_by(DtePaymentDataModel.id.desc())
            .first()
        )
        if not payment:
            return None
        if payment.dte_id:
            dte = self.db.query(DteModel).filter(DteModel.id == payment.dte_id).first()
            if dte:
                return dte
        if payment.folio:
            return (
                self.db.query(DteModel)
                .filter(DteModel.folio == payment.folio)
                .order_by(DteModel.id.desc())
                .first()
            )
        return None


def _clean_pay_id(pay_id: str) -> str:
    cleaned = unquote((pay_id or "").strip()).strip("/")
    for junk in ("{{1}}", "{{ 1 }}", "%7B%7B1%7D%7D", "{1}"):
        cleaned = cleaned.replace(junk, "")
    return cleaned.strip().strip("/")


def _client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64] or None
    if request.client and request.client.host:
        return request.client.host[:64]
    return None


def _user_agent(request: Request | None) -> str | None:
    if request is None:
        return None
    agent = request.headers.get("user-agent")
    return agent[:512] if agent else None
