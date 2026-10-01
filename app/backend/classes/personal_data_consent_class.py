"""Guarda la aceptacion del aviso de datos personales como un formulario."""

from __future__ import annotations

import json
from datetime import datetime
from urllib.parse import unquote

import pytz
from fastapi import Request
from sqlalchemy.orm import Session

from app.backend.classes.payment_gateway_class import normalize_gateway_order_id
from app.backend.db.models import (
    CustomerModel,
    DteModel,
    DtePaymentDataModel,
    PersonalDataConsentModel,
    PersonalDataConsentTypeModel,
)

TYPE_DTE_PAYMENT = "dte_payment"
TYPE_WEB = "web"

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
        """True si este RUT ya acepto el consentimiento de pago."""
        cleaned = _clean_pay_id(pay_id)
        dte = self._resolve_dte(cleaned)
        rut = str(dte.rut).strip() if dte and dte.rut else ""
        if not rut:
            return False
        payment_type = self._type_or_none(TYPE_DTE_PAYMENT)
        if payment_type is None:
            return False
        row = (
            self.db.query(PersonalDataConsentModel.id)
            .filter(PersonalDataConsentModel.accepted == 1)
            .filter(PersonalDataConsentModel.consent_type_id == payment_type.id)
            .filter(PersonalDataConsentModel.rut == rut)
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
        now = datetime.now(_TZ).replace(tzinfo=None)
        case_description = "Aceptacion para continuar al pago."
        consent_type = self._type(TYPE_DTE_PAYMENT)
        form = {
            "acepta": True,
            "origen": consent_type.name,
            "nombre": getattr(customer, "customer", None) if customer else None,
            "rut": (dte.rut if dte and dte.rut else None) or (getattr(customer, "rut", None) if customer else None),
            "telefono": getattr(customer, "phone", None) if customer else None,
            "correo": getattr(customer, "email", None) if customer else None,
            "descripcion_del_caso": case_description,
            "dia": _WEEKDAYS[now.weekday()],
            "fecha": now.strftime("%Y-%m-%d"),
            "hora": now.strftime("%H:%M:%S"),
            "declaracion": CONSENT_STATEMENT,
        }

        row = PersonalDataConsentModel(
            consent_type_id=consent_type.id,
            accepted=1,
            rut=form["rut"],
            customer_name=form["nombre"],
            email=form["correo"],
            phone=form["telefono"],
            customer_id=getattr(customer, "id", None) if customer else None,
            case_description=case_description,
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

    def _type(self, code: str) -> PersonalDataConsentTypeModel:
        row = self._type_or_none(code)
        if row is None:
            raise RuntimeError(f"Falta el tipo de consentimiento {code}")
        return row

    def _type_or_none(self, code: str) -> PersonalDataConsentTypeModel | None:
        return (
            self.db.query(PersonalDataConsentTypeModel)
            .filter(PersonalDataConsentTypeModel.code == code)
            .first()
        )

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
