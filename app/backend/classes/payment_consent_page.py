"""Pantalla de consentimiento servida en el mismo enlace de pago, sin pasar por el login."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from html import escape
from urllib.parse import unquote

import pytz
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.backend.classes.payments_env import payments_env
from app.backend.db.models import PaymentConsentChallengeModel

_TZ = pytz.timezone("America/Santiago")
_CHALLENGE_MINUTES = 20


def clean_pay_id(pay_id: str) -> str:
    cleaned = unquote((pay_id or "").strip()).strip("/")
    for junk in ("{{1}}", "{{ 1 }}", "%7B%7B1%7D%7D", "{1}"):
        cleaned = cleaned.replace(junk, "")
    return cleaned.strip().strip("/")


def _now():
    return datetime.now(_TZ).replace(tzinfo=None)


def issue_challenge(db: Session, pay_id: str) -> str:
    token = secrets.token_urlsafe(32)
    now = _now()
    db.add(
        PaymentConsentChallengeModel(
            token=token,
            pay_id=pay_id,
            expires_at=now + timedelta(minutes=_CHALLENGE_MINUTES),
            added_date=now,
        )
    )
    db.commit()
    return token


def challenge_is_valid(db: Session, pay_id: str, token: str) -> bool:
    now = _now()
    row = (
        db.query(PaymentConsentChallengeModel)
        .filter(
            PaymentConsentChallengeModel.token == (token or "").strip(),
            PaymentConsentChallengeModel.pay_id == pay_id,
            PaymentConsentChallengeModel.used_at.is_(None),
            PaymentConsentChallengeModel.expires_at >= now,
        )
        .first()
    )
    return row is not None


def consume_challenge(db: Session, pay_id: str, token: str) -> bool:
    now = _now()
    row = (
        db.query(PaymentConsentChallengeModel)
        .filter(
            PaymentConsentChallengeModel.token == (token or "").strip(),
            PaymentConsentChallengeModel.pay_id == pay_id,
            PaymentConsentChallengeModel.used_at.is_(None),
            PaymentConsentChallengeModel.expires_at >= now,
        )
        .first()
    )
    if not row:
        return False
    row.used_at = now
    db.commit()
    return True


def _submit_url() -> str:
    base = payments_env(
        "PAYMENTS_PUBLIC_API_BASE",
        default="https://intrajisbackend.com/api",
    ).rstrip("/")
    return f"{base}/payments/consent/submit"


def render_consent_page(pay_id: str, challenge: str, error: str = "") -> HTMLResponse:
    safe_pay = escape(pay_id, quote=True)
    safe_challenge = escape(challenge, quote=True)
    safe_action = escape(_submit_url(), quote=True)
    error_html = (
        f'<p class="error">{escape(error)}</p>' if error else ""
    )
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Consentimiento para continuar al pago</title>
  <style>
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: #f4f7fb; color: #1a2332; }}
    .wrap {{ max-width: 640px; margin: 0 auto; padding: 28px 16px 40px; }}
    h1 {{ font-size: 22px; margin: 0 0 8px; }}
    .lead {{ margin: 0 0 16px; color: #5a6577; font-size: 14px; }}
    .notice {{ background: #e8f1fb; border: 1px solid #d3e3f6; border-radius: 10px; padding: 16px 18px; color: #1e3a5f; font-size: 15px; line-height: 1.55; }}
    .notice p {{ margin: 0 0 12px; }}
    .notice p:last-child {{ margin-bottom: 0; }}
    label {{ display: flex; gap: 10px; align-items: flex-start; margin-top: 16px; font-size: 15px; line-height: 1.45; }}
    button {{ margin-top: 18px; width: 100%; border: 0; border-radius: 8px; padding: 14px 16px; font-size: 16px; font-weight: 700; color: #fff; background: #1565c0; cursor: pointer; }}
    button:disabled {{ background: #9bb8d3; cursor: not-allowed; }}
    .error {{ background: #fdecea; color: #8a1f11; border-radius: 8px; padding: 10px 12px; margin: 0 0 12px; }}
    a {{ color: #1565c0; }}
  </style>
</head>
<body>
  <main class="wrap">
    <h1>Antes de continuar al pago</h1>
    <p class="lead">Lee la información y acepta el tratamiento de tus datos para seguir.</p>
    {error_html}
    <form method="post" action="{safe_action}">
      <input type="hidden" name="pay_id" value="{safe_pay}">
      <input type="hidden" name="challenge" value="{safe_challenge}">
      <div class="notice">
        <p><strong>Tratamiento de datos personales (Ley N° 21.719)</strong></p>
        <p>JIS Parking tratará sus datos personales esenciales —nombre, RUT, teléfono, correo electrónico, descripción del caso, fecha/lugar del suceso y adjuntos— para <em>registrar, gestionar y responder</em> su sugerencia, reclamo o felicitación, y para darle seguimiento por correo, WhatsApp o el portal de seguimiento.</p>
        <p>La base legal es su <strong>consentimiento</strong> previo, libre, específico e inequívoco. No usaremos estos datos para marketing. Puede ejercer sus derechos de acceso, rectificación, supresión, oposición, portabilidad y bloqueo, y <strong>revocar este consentimiento</strong> en cualquier momento, escribiendo a <a href="mailto:contacto@jisparking.com">contacto@jisparking.com</a> o en nuestra Política de Privacidad.</p>
      </div>
      <label>
        <input id="accepted" type="checkbox" name="accepted" value="1">
        <span>He leído la información anterior y autorizo el tratamiento de mis datos personales para las finalidades indicadas.</span>
      </label>
      <button id="continue" type="submit" disabled>Continuar al pago</button>
    </form>
  </main>
  <script>
    var box = document.getElementById('accepted');
    var button = document.getElementById('continue');
    box.addEventListener('change', function () {{ button.disabled = !box.checked; }});
  </script>
</body>
</html>"""
    return HTMLResponse(
        content=html,
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


def render_message(title: str, message: str, status_code: int = 400) -> HTMLResponse:
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: #f4f7fb; color: #1a2332; }}
    .wrap {{ max-width: 640px; margin: 0 auto; padding: 48px 16px; }}
  </style>
</head>
<body>
  <main class="wrap">
    <h1>{escape(title)}</h1>
    <p>{escape(message)}</p>
  </main>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=status_code, headers={"Cache-Control": "no-store"})
