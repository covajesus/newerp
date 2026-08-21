"""SII BTE (Boleta de prestación de servicios de terceros) portal client.

Automates zeus.sii.cl/cvc/bte with RUT + Clave Tributaria (same approach as
LibreDTE API Gateway / BaseAPI). Not a DTE/CAF flow.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from html import unescape
from urllib.parse import urljoin

import httpx

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
_BASE = "https://zeus.sii.cl"
_TARGET_EMIT = f"{_BASE}/cvc_cgi/bte/bte_indiv_ing"
_TARGET_CONS = f"{_BASE}/cvc_cgi/bte/bte_indiv_cons?1"
_TARGET_ANULA = f"{_BASE}/cvc_cgi/bte/bte_indiv_anula"

# Retención vigente 2026 (Ley 21.133). El SII puede devolver el monto exacto.
RETENCION_PCT_2026 = 15.25

ANNUL_CAUSES = {
    "prestacion_no_efectuada": "1",
    "error_digitacion": "2",
}


@dataclass
class BteEmitResult:
    folio: int
    issue_date: str
    beneficiary_rut: str
    beneficiary_name: str
    service: str
    monto_bruto: int
    retencion: int
    liquido: int
    status: str = "emitida"


@dataclass
class BteListItem:
    folio: int | None
    issue_date: str | None
    beneficiary_rut: str | None
    beneficiary_name: str | None
    service: str | None
    monto_bruto: int | None
    retencion: int | None
    liquido: int | None
    status: str = "emitida"


def retention_amount(bruto: int, pct: float = RETENCION_PCT_2026) -> int:
    return int(round(bruto * (pct / 100.0)))


def liquido_amount(bruto: int, pct: float = RETENCION_PCT_2026) -> int:
    return int(bruto) - retention_amount(bruto, pct)


def validate_login(*, rut: str, password: str, timeout: float = 45.0) -> bool:
    """Authenticate against SII with Clave Tributaria; returns True if session cookies appear."""
    with _session(timeout) as client:
        _login(client, rut, password, _TARGET_EMIT)
        return _has_livewire(client)


def emit_bte(
    *,
    login_rut: str,
    password: str,
    beneficiary_rut: str,
    beneficiary_name: str,
    domicilio: str,
    region: int,
    comuna: int,
    servicio: str,
    monto: int,
    issue_date: date | None = None,
    timeout: float = 90.0,
) -> BteEmitResult:
    if int(monto) < 1:
        raise ValueError("El monto debe ser al menos 1")
    ben_body, ben_dv = _split_rut(beneficiary_rut)
    if int(ben_body) > 49_999_999:
        raise ValueError("El RUT del beneficiario debe ser de persona natural")
    when = issue_date or date.today()
    comuna_name = _comuna_name(int(region), int(comuna)) or ""

    last_err: Exception | None = None
    for attempt in range(3):
        try:
            return _emit_bte_once(
                login_rut=login_rut,
                password=password,
                ben_body=ben_body,
                ben_dv=ben_dv,
                beneficiary_name=beneficiary_name,
                domicilio=domicilio,
                region=int(region),
                comuna=int(comuna),
                comuna_name=comuna_name,
                servicio=servicio,
                monto=int(monto),
                when=when,
                timeout=timeout,
            )
        except httpx.HTTPError as exc:
            last_err = exc
            continue
    raise RuntimeError(f"Error de red al emitir BTE: {last_err}")


def _emit_bte_once(
    *,
    login_rut: str,
    password: str,
    ben_body: str,
    ben_dv: str,
    beneficiary_name: str,
    domicilio: str,
    region: int,
    comuna: int,
    comuna_name: str,
    servicio: str,
    monto: int,
    when: date,
    timeout: float,
) -> BteEmitResult:
    with _session(timeout) as client:
        _login(client, login_rut, password, _TARGET_EMIT)
        r0 = client.get(_TARGET_EMIT)
        html = r0.text or ""
        if _needs_login(html) or "no se encuentra autenticado" in html.lower():
            raise RuntimeError("Sesión SII inválida al abrir emisión de BTE. Verifique la clave.")

        # Paso 1 → bte_indiv_ing2 (borrador / confirmación)
        fields1 = {
            **_extract_inputs(html),
            "DIA": f"{when.day:02d}",
            "MES": f"{when.month:02d}",
            "ANO": str(when.year),
            "RUT_TERC": ben_body,
            "DV_TERC": ben_dv,
            "NOMBRE_TERC": (beneficiary_name or "").strip(),
            "DOMICILIO_TER": (domicilio or "").strip(),
            "cod_region": str(region),
            "cod_comuna": str(comuna),
            "DESC_COMUNA": comuna_name,
            "PRESTA1": (servicio or "").strip(),
            "VALOR1": str(monto),
            "PRESTA2": "",
            "VALOR2": "",
            "PRESTA3": "",
            "VALOR3": "",
            "PRESTA4": "",
            "VALOR4": "",
            "ACEPTAR": "Continuar",
        }
        em_body, em_dv = _split_rut(login_rut)
        fields1.setdefault("RUT", em_body)
        fields1.setdefault("DV", em_dv)

        action1 = _extract_form_action(html) or "/cvc_cgi/bte/bte_indiv_ing2"
        html2 = _post(client, action1, fields1, referer=_TARGET_EMIT)
        hard = _classify_error(html2)
        if hard:
            raise RuntimeError(hard)

        inputs2 = _extract_inputs(html2)
        if "BRT" not in inputs2 and "Emitir la Boleta" not in html2:
            err = _extract_plain_error(html2) or "El SII no devolvió el borrador de la BTE."
            raise RuntimeError(err)

        # Paso 2 → bte_indiv_ing3 (emisión real)
        fields2 = {**inputs2, "ACEPTAR": "Emitir la Boleta"}
        action2 = _extract_form_action(html2) or "/cvc_cgi/bte/bte_indiv_ing3"
        html3 = _post(
            client,
            action2,
            fields2,
            referer=urljoin(_BASE + "/", action1.lstrip("/")),
        )
        hard = _classify_error(html3)
        if hard:
            raise RuntimeError(hard)

        folio = _extract_folio(html3)
        if folio is None:
            err = _extract_plain_error(html3) or "El SII no confirmó la emisión de la BTE."
            raise RuntimeError(err)

        bruto = _parse_int(inputs2.get("BRT")) or monto
        ret = _parse_int(inputs2.get("IMP")) or retention_amount(bruto)
        liq = _parse_int(inputs2.get("NET")) or liquido_amount(bruto)
        nombre = (inputs2.get("NOMBRE_TERC") or beneficiary_name or "").strip()

        return BteEmitResult(
            folio=folio,
            issue_date=when.isoformat(),
            beneficiary_rut=f"{ben_body}-{ben_dv}",
            beneficiary_name=nombre,
            service=(servicio or "").strip(),
            monto_bruto=bruto,
            retencion=ret,
            liquido=liq,
            status="emitida",
        )


def list_emitted(
    *,
    login_rut: str,
    password: str,
    year: int,
    month: int,
    timeout: float = 90.0,
) -> list[BteListItem]:
    if not (1 <= int(month) <= 12):
        raise ValueError("Mes inválido")
    with _session(timeout) as client:
        _login(client, login_rut, password, _TARGET_CONS)
        r0 = client.get(_TARGET_CONS)
        html = r0.text or ""
        if _needs_login(html) or "no se encuentra autenticado" in html.lower():
            raise RuntimeError("Sesión SII inválida al consultar BTE emitidas.")

        fields = {
            **_extract_inputs(html),
            "TIPO": "mensual",
            "ano": str(int(year)),
            "mes": f"{int(month):02d}",
            "ANO": str(int(year)),
            "MES": f"{int(month):02d}",
        }
        action = _extract_form_action(html) or "/cvc_cgi/bte/bte_indiv_cons"
        html = _post(client, action, fields, referer=_TARGET_CONS)
        hard = _classify_error(html)
        if hard and "no hay" not in hard.lower() and "sin inform" not in hard.lower():
            # empty period is ok
            if "autorizad" in hard.lower() or "autentic" in hard.lower():
                raise RuntimeError(hard)
        return _parse_emitidas_table(html)


def annul_bte(
    *,
    login_rut: str,
    password: str,
    folio: int,
    cause: str = "error_digitacion",
    timeout: float = 90.0,
) -> None:
    motivo = ANNUL_CAUSES.get(cause) or ANNUL_CAUSES["error_digitacion"]
    with _session(timeout) as client:
        _login(client, login_rut, password, _TARGET_ANULA)
        r0 = client.get(_TARGET_ANULA)
        html = r0.text or ""
        if _needs_login(html) or "no se encuentra autenticado" in html.lower():
            raise RuntimeError("Sesión SII inválida al anular BTE.")

        fields = {
            **_extract_inputs(html),
            "NUMBOL": str(int(folio)),
            "NUMERO": str(int(folio)),
            "MOTIVO": motivo,
        }
        action = _extract_form_action(html) or "/cvc_cgi/bte/bte_indiv_anula"
        html = _post(client, action, fields, referer=_TARGET_ANULA)

        # Confirm if needed
        if "confirm" in html.lower() or "ACEPTAR" in html:
            inputs = _extract_inputs(html)
            act2 = _extract_form_action(html) or action
            confirm = {**inputs, "ACEPTAR": inputs.get("ACEPTAR") or "Aceptar"}
            html = _post(client, act2, confirm, referer=_TARGET_ANULA)

        hard = _classify_error(html)
        low = (html or "").lower()
        if hard and "anulad" not in low:
            raise RuntimeError(hard)
        if "anulad" not in low and "exitos" not in low and folio and str(folio) not in html:
            # Some pages just redisplay without clear success text
            if "error" in low or "no es posible" in low or "no se puede" in low:
                raise RuntimeError(_extract_plain_error(html) or "No se pudo anular la BTE.")


def _session(timeout: float) -> httpx.Client:
    return httpx.Client(
        timeout=timeout,
        verify=False,
        follow_redirects=True,
        headers={
            "User-Agent": _UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-CL,es;q=0.9",
        },
    )


def _login(client: httpx.Client, rut: str, password: str, target: str) -> None:
    body, dv = _split_rut(rut)
    rutcntr = f"{body}-{dv}"
    # Warm cookies
    client.get(
        "https://zeusr.sii.cl/AUT2000/InicioAutenticacion/"
        f"IngresoRutClave.html?{target}"
    )
    # Password login: POST form (GET often does not set NETSCAPE_LIVEWIRE).
    data = {
        "rutcntr": rutcntr,
        "rut": body,
        "dv": dv,
        "clave": password,
        "referencia": target,
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://zeusr.sii.cl",
        "Referer": (
            "https://zeusr.sii.cl/AUT2000/InicioAutenticacion/"
            f"IngresoRutClave.html?{target}"
        ),
    }
    r = client.post(
        "https://zeusr.sii.cl/cgi_AUT2000/CAutInicio.cgi",
        data=data,
        headers=headers,
    )
    text = r.text or ""
    if "clave incorrecta" in text.lower() or "clave inválida" in text.lower():
        raise RuntimeError("Clave Tributaria inválida según el SII.")
    if "bloquead" in text.lower():
        raise RuntimeError("Clave Tributaria bloqueada en el SII.")
    if "máximo de sesiones" in text.lower() or "maximo de sesiones" in text.lower():
        raise RuntimeError(
            "Límite de sesiones del SII alcanzado. Cierre sesión en sii.cl y reintente."
        )
    if not _has_livewire(client):
        client.post(
            "https://herculesr.sii.cl/cgi_AUT2000/CAutInicio.cgi",
            data=data,
            headers=headers,
        )
    if not _has_livewire(client):
        raise RuntimeError(
            "No se pudo autenticar en el SII con RUT + Clave Tributaria "
            "(sin cookies NETSCAPE_LIVEWIRE)."
        )


def _has_livewire(client: httpx.Client) -> bool:
    return any(k.startswith("NETSCAPE_LIVEWIRE") for k in client.cookies.keys())


def _post(
    client: httpx.Client,
    action: str,
    fields: dict[str, str],
    referer: str | None = None,
) -> str:
    if action.startswith("http"):
        url = action
    else:
        url = urljoin(_BASE + "/", action.lstrip("/"))
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": _BASE,
        "Referer": referer or _BASE + "/cvc/bte/menu.html",
    }
    # Drop empty button-only noise carefully — keep empty VALOR/PRESTA
    r = client.post(url, data=fields, headers=headers)
    return r.text or ""


def _split_rut(rut: str) -> tuple[str, str]:
    clean = re.sub(r"[.\s]", "", (rut or "").strip().upper())
    if "-" in clean:
        body, dig = clean.rsplit("-", 1)
    else:
        body, dig = clean[:-1], clean[-1:]
    body = re.sub(r"\D", "", body)
    if not body or not dig:
        raise ValueError("RUT inválido")
    return body, dig


def _needs_login(html: str) -> bool:
    return any(
        x in (html or "")
        for x in ("IngresoRutClave", "IngresoCertificado", "AUT2000/InicioAutenticacion")
    )


def _extract_form_action(html: str) -> str | None:
    m = re.search(r"<form[^>]*\saction=['\"]([^'\"]+)['\"]", html or "", flags=re.I)
    return unescape(m.group(1)) if m else None


def _extract_inputs(html: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(r"<input\b([^>]*)>", html or "", flags=re.I):
        attrs = m.group(1)
        name_m = re.search(r"\bname=['\"]([^'\"]+)['\"]", attrs, flags=re.I)
        if not name_m:
            continue
        name = unescape(name_m.group(1))
        val_m = re.search(r"\bvalue=['\"]([^'\"]*)['\"]", attrs, flags=re.I)
        out[name] = unescape(val_m.group(1)) if val_m else ""
    for m in re.finditer(
        r"<select\b[^>]*\bname=['\"]([^'\"]+)['\"][^>]*>(.*?)</select>",
        html or "",
        flags=re.I | re.S,
    ):
        name = unescape(m.group(1))
        block = m.group(2)
        sel = re.search(
            r"<option[^>]*selected[^>]*value=['\"]([^'\"]*)['\"]",
            block,
            flags=re.I,
        ) or re.search(
            r"<option[^>]*value=['\"]([^'\"]*)['\"][^>]*selected",
            block,
            flags=re.I,
        )
        if sel:
            out[name] = unescape(sel.group(1))
    return out


def _looks_like_folio(html: str) -> bool:
    return _extract_folio(html) is not None


def _extract_folio(html: str) -> int | None:
    text = unescape(html or "")
    patterns = (
        r"N[°º.]?\s*(\d{1,10})",
        r"n[uú]mero\s+de\s+(?:la\s+)?boleta[^0-9]{0,40}(\d{1,10})",
        r"folio[^0-9]{0,20}(\d{1,10})",
        r"boleta\s+n[°º.]?\s*(\d{1,10})",
        r"NUMBOL[^0-9]{0,20}(\d{1,10})",
    )
    for pat in patterns:
        m = re.search(pat, text, flags=re.I)
        if m:
            try:
                val = int(m.group(1))
                if val > 0:
                    return val
            except ValueError:
                continue
    # Hidden input after emission
    inputs = _extract_inputs(html)
    num = _parse_int(inputs.get("NUMBOL"))
    return num if num and num > 0 else None


def _parse_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    digits = re.sub(r"[^\d]", "", str(value))
    try:
        return int(digits) if digits else None
    except ValueError:
        return None


def _comuna_name(region: int, comuna: int) -> str | None:
    try:
        from app.backend.classes.sii.bte_communes import REGIONS

        return REGIONS.get(region, {}).get(comuna)
    except Exception:
        return None


def _extract_int_near(html: str, label_re: str) -> int | None:
    plain = re.sub(r"<[^>]+>", " ", unescape(html or ""))
    plain = re.sub(r"\s+", " ", plain)
    m = re.search(label_re + r"[^0-9]{0,40}([\d.]{1,15})", plain, flags=re.I)
    if not m:
        return None
    digits = re.sub(r"[^\d]", "", m.group(1))
    return int(digits) if digits else None


def _classify_error(html: str) -> str | None:
    if not html:
        return None
    plain = re.sub(r"<[^>]+>", " ", unescape(html))
    plain = re.sub(r"\s+", " ", plain).strip()
    low = plain.lower()
    if "no se encuentra autenticado" in low:
        return "Sesión SII expirada o no autenticada para BTE."
    if "no est" in low and "autorizad" in low:
        return plain[:400]
    if "clave incorrecta" in low or "clave inválida" in low:
        return "Clave Tributaria inválida."
    if "no ha sido posible" in low:
        m = re.search(r"No ha sido posible[^.]*\.", plain, flags=re.I)
        return (m.group(0) if m else plain)[:400]
    return None


def _extract_plain_error(html: str) -> str | None:
    plain = re.sub(r"<[^>]+>", " ", unescape(html or ""))
    plain = re.sub(r"\s+", " ", plain).strip()
    return plain[:400] if plain else None


def _parse_emitidas_table(html: str) -> list[BteListItem]:
    """Best-effort parse of SII HTML table for emitted BTEs."""
    items: list[BteListItem] = []
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html or "", flags=re.I | re.S)
    for row in rows:
        cells = [
            re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(c))).strip()
            for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, flags=re.I | re.S)
        ]
        if len(cells) < 3:
            continue
        # Skip header-ish rows
        joined = " ".join(cells).lower()
        if "folio" in joined and "rut" in joined:
            continue
        folio = None
        for c in cells[:3]:
            digits = re.sub(r"[^\d]", "", c)
            if digits and len(digits) <= 10:
                try:
                    folio = int(digits)
                    break
                except ValueError:
                    pass
        if folio is None:
            continue
        fecha = next((c for c in cells if re.match(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", c)), None)
        rut = next((c for c in cells if re.match(r"^\d{1,8}-[\dkK]$", c.replace(".", ""))), None)
        montos = []
        for c in cells:
            d = re.sub(r"[.\s]", "", c)
            if re.fullmatch(r"\d{3,}", d):
                montos.append(int(d))
        status = "anulada" if "anul" in joined else "emitida"
        items.append(
            BteListItem(
                folio=folio,
                issue_date=_normalize_date(fecha) if fecha else None,
                beneficiary_rut=rut.replace(".", "").upper() if rut else None,
                beneficiary_name=None,
                service=None,
                monto_bruto=montos[0] if montos else None,
                retencion=montos[1] if len(montos) > 1 else None,
                liquido=montos[2] if len(montos) > 2 else None,
                status=status,
            )
        )
    return items


def _normalize_date(value: str) -> str:
    m = re.match(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", value.strip())
    if not m:
        return value
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if y < 100:
        y += 2000
    return f"{y:04d}-{mo:02d}-{d:02d}"
