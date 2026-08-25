from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime

import requests
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.backend.db.database import get_db
from app.backend.db.models import SiiCommuneModel, SiiRegionModel

sii_geo = APIRouter(prefix="/sii", tags=["SII Geo"])

SII_RSS_URL = "https://zeus.sii.cl/admin/rss/sii_ind_rss.xml"


@sii_geo.get("/regions")
def list_sii_regions(db: Session = Depends(get_db)):
    """Catálogo regiones SII BTE. Shape compatible con selects (id + region)."""
    rows = db.query(SiiRegionModel).order_by(SiiRegionModel.id).all()
    return {
        "message": [
            {
                "id": r.id,
                "region": r.name,
                "region_id": r.region_id,
            }
            for r in rows
        ]
    }


@sii_geo.get("/communes/{sii_region_id}")
def list_sii_communes(sii_region_id: int, db: Session = Depends(get_db)):
    """Comunas SII de una región. Shape compatible (id + commune)."""
    rows = (
        db.query(SiiCommuneModel)
        .filter(SiiCommuneModel.sii_region_id == sii_region_id)
        .order_by(SiiCommuneModel.name)
        .all()
    )
    return {
        "message": [
            {
                "id": c.id,
                "commune": c.name,
                "region_id": c.sii_region_id,
                "commune_id": c.commune_id,
            }
            for c in rows
        ]
    }


def _format_clp_value(raw: str) -> str:
    """Formatea valor del RSS (ej. 952.37 o 38.123,45) a estilo chileno."""
    numeric_value = (raw or "").strip()
    if not numeric_value:
        return "N/D"
    clean = re.sub(r"[^\d]", "", numeric_value)
    if not clean:
        return "N/D"
    number = float(clean)
    has_decimals = False
    decimal_places = 0
    if "." in numeric_value:
        last = numeric_value.split(".")[-1]
        if last.isdigit() and len(last) <= 2 and "," not in last:
            has_decimals = True
            decimal_places = len(last)
    if has_decimals:
        real = number / (10**decimal_places)
        formatted = f"{real:,.{decimal_places}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"$ {formatted}"
    # entero con separador de miles
    return f"$ {int(number):,}".replace(",", ".")


def _parse_sii_rss(xml_text: str) -> dict:
    root = ET.fromstring(xml_text)
    indicators: dict[str, dict[str, str]] = {}
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        description = item.findtext("description") or ""
        pub_date = item.findtext("pubDate") or ""

        value = "N/D"
        match = re.search(r"CLP - \$\s*([\d,.]+)", description)
        if match:
            value = _format_clp_value(match.group(1))

        date_str = ""
        if pub_date:
            try:
                date_str = parsedate_to_datetime(pub_date).strftime("%d-%m-%Y")
            except Exception:
                try:
                    date_str = datetime.fromisoformat(pub_date).strftime("%d-%m-%Y")
                except Exception:
                    date_str = pub_date

        title_u = title.upper().strip()
        if title_u == "DOLAR OBSERVADO":
            indicators["dolar"] = {"value": value, "date": date_str}
        elif title_u == "U.F.":
            indicators["uf"] = {"value": value, "date": date_str}
        elif "U.T.M." in title_u:
            indicators["utm"] = {"value": value, "date": date_str, "title": title}
        elif "EURO" in title_u:
            indicators["euro"] = {"value": value, "date": date_str}
    return indicators


@sii_geo.get("/indicators")
def sii_indicators():
    """
    Indicadores SII (Dólar, UF, UTM) desde el RSS oficial.
    Se consulta en backend para evitar CORS / proxies externos inestables.
    """
    try:
        response = requests.get(
            SII_RSS_URL,
            timeout=15,
            headers={"User-Agent": "IntraJIS/1.0 (+https://intrajis.com)"},
        )
        if response.status_code != 200 or not response.text:
            return {
                "message": {
                    "status": "error",
                    "indicators": {},
                    "detail": f"RSS SII HTTP {response.status_code}",
                }
            }
        indicators = _parse_sii_rss(response.text)
        return {
            "message": {
                "status": "success",
                "indicators": indicators,
            }
        }
    except Exception as exc:
        return {
            "message": {
                "status": "error",
                "indicators": {},
                "detail": str(exc),
            }
        }
