"""Reutiliza y reemite NC rechazadas de noviembre con el mismo folio."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.backend.classes.customer_class import CustomerClass
from app.backend.classes.customer_ticket_class import (
    SIMPLEFACTURA_AMBIENTE,
    SIMPLEFACTURA_RUT_EMISOR,
    SIMPLEFACTURA_SUCURSAL,
    CustomerTicketClass,
)
from app.backend.classes.folio_class import FolioClass
from app.backend.db.database import SessionLocal
from app.backend.db.models import BranchOfficeModel, DteModel

REJECTED = [
    6915,
    6916,
    6917,
    6939,
    6941,
    6942,
    6944,
    6961,
    6962,
    6963,
    6964,
    6965,
    6966,
    6967,
    6971,
]


def reuse_folio(token: str, folio: int) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "credenciales": {
            "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
            "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
        },
        "codigoTipoDte": 61,
        "folio": int(folio),
        "ambiente": SIMPLEFACTURA_AMBIENTE,
    }
    try:
        r = requests.post(
            "https://api.simplefactura.cl/folios/reutilizar",
            json=payload,
            headers=headers,
            timeout=180,
        )
    except requests.Timeout:
        return {"http": 0, "body": {"timeout": True, "message": "timeout reutilizar"}}
    except requests.RequestException as exc:
        return {"http": 0, "body": {"error": str(exc)}}
    try:
        body = r.json() if r.text else {}
    except ValueError:
        body = {"raw": (r.text or "")[:400]}
    return {"http": r.status_code, "body": body}


def is_reused(flag) -> bool:
    return str(flag or "").strip().lower() in ("si", "sí", "yes", "true", "1")


def already_reissued(status: dict) -> bool:
    """True si ya no está en el rechazo original de nov (reemitida hoy u otra)."""
    estado = str(status.get("estadoSII") or "")
    fecha = str(status.get("fechaDte") or "")
    if "Rechazado" in estado:
        return False
    # Tras reemitir suele quedar Emisión / Aceptado con fecha de hoy
    if "2026-11-04" in fecha or "04-11-2026" in fecha:
        return True
    if "Aceptado" in estado or "Emisi" in estado:
        return True
    return False


def sf_nc_status(token: str, folio: int) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    r = requests.post(
        "https://api.simplefactura.cl/documentIssued",
        json={
            "credenciales": {
                "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
                "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
            },
            "dteReferenciadoExterno": {
                "folio": int(folio),
                "codigoTipoDte": 61,
                "ambiente": SIMPLEFACTURA_AMBIENTE,
            },
        },
        headers=headers,
        timeout=60,
    )
    body = r.json() if r.text else {}
    data = body.get("data") if isinstance(body, dict) else {}
    if not isinstance(data, dict):
        data = {}
    return {
        "estadoSII": data.get("estadoSII"),
        "folioReutilizado": data.get("folioReutilizado"),
        "fechaDte": data.get("fechaDte"),
        "trackId": data.get("trackId"),
    }


def main() -> None:
    db = SessionLocal()
    ticket = CustomerTicketClass(db)
    folio_cls = FolioClass(db)
    try:
        token, err = ticket._v2_bearer_token()
        if not token:
            print("NO TOKEN", err)
            return

        results = []
        for nc_folio in REJECTED:
            print("=" * 60, "NC", nc_folio)
            try:
                nc = (
                    db.query(DteModel)
                    .filter(DteModel.dte_type_id == 61, DteModel.folio == nc_folio)
                    .order_by(DteModel.id.desc())
                    .first()
                )
                if not nc or not nc.denied_folio:
                    print("SKIP: sin NC local / denied_folio")
                    results.append({"folio": nc_folio, "status": "skip_no_local"})
                    continue

                ref = (
                    db.query(DteModel)
                    .filter(
                        DteModel.folio == int(nc.denied_folio),
                        DteModel.dte_type_id.in_([33, 39]),
                    )
                    .order_by(DteModel.id.desc())
                    .first()
                )
                if not ref:
                    print("SKIP: sin DTE referenciado", nc.denied_folio)
                    results.append({"folio": nc_folio, "status": "skip_no_ref"})
                    continue

                ref_type = int(ref.dte_type_id)
                branch = (
                    db.query(BranchOfficeModel)
                    .filter(BranchOfficeModel.id == ref.branch_office_id)
                    .first()
                )
                if not branch:
                    print("SKIP: sin sucursal", ref.branch_office_id)
                    results.append({"folio": nc_folio, "status": "skip_no_branch"})
                    continue

                customer = CustomerClass(db).get_by_rut(ref.rut)
                customer_data = json.loads(customer)
                if "customer_data" not in customer_data:
                    print("SKIP: sin cliente", ref.rut)
                    results.append({"folio": nc_folio, "status": "skip_no_customer"})
                    continue

                before = sf_nc_status(token, nc_folio)
                print("before", before)
                if already_reissued(before):
                    print("SKIP: ya reemitida", before)
                    results.append(
                        {
                            "folio": nc_folio,
                            "status": "already_reissued",
                            "sf_final": before,
                        }
                    )
                    continue

                # 1) Reutilizar en SF si aún no está marcado
                if not is_reused(before.get("folioReutilizado")):
                    reuse = reuse_folio(token, nc_folio)
                    print(
                        "reutilizar",
                        reuse.get("http"),
                        json.dumps(reuse.get("body"), ensure_ascii=False)[:300],
                    )
                    token, _ = ticket._v2_bearer_token()
                    time.sleep(2)
                    after_reuse = sf_nc_status(token, nc_folio)
                    print("after_reuse", after_reuse)
                    if not is_reused(after_reuse.get("folioReutilizado")):
                        if (reuse.get("body") or {}).get("timeout"):
                            print("reintento reutilizar tras timeout")
                            reuse2 = reuse_folio(token, nc_folio)
                            print(
                                "reutilizar2",
                                reuse2.get("http"),
                                json.dumps(reuse2.get("body"), ensure_ascii=False)[:300],
                            )
                            time.sleep(2)
                            after_reuse = sf_nc_status(token, nc_folio)
                            print("after_reuse2", after_reuse)
                        if not is_reused(after_reuse.get("folioReutilizado")):
                            print("WARN: no quedó reutilizado; se intenta emitir igual")
                else:
                    print("ya reutilizado en SF")

                # 2) Armar NC con MISMO folio + FchRef real SF
                gross = int(ref.cash_amount) if ref.cash_amount else int(ref.total or 0)
                ref_date = ticket._resolve_referenced_dte_fchref(ref, ref_type)
                document = ticket._build_subscriber_credit_note_document_v2(
                    customer_data,
                    branch,
                    ref_dte_type=ref_type,
                    ref_folio=ref.folio,
                    ref_date=ref_date,
                    gross_amount=gross,
                    nc_folio=nc_folio,
                )
                print(
                    "emit folio=",
                    nc_folio,
                    "ref=",
                    ref_type,
                    ref.folio,
                    "FchRef=",
                    document["Referencia"][0]["FchRef"],
                    "total=",
                    gross,
                )

                emit = ticket.emit_credit_note_v2(document, branch)
                print(
                    "emit_status=",
                    emit.get("status"),
                    "msg=",
                    str(emit.get("message") or "")[:200],
                    "http=",
                    emit.get("http_status"),
                    "folio_resp=",
                    emit.get("folio"),
                )

                # 3) Marcar pool local usada con este folio
                pool = db.execute(
                    text(
                        """
                        SELECT id FROM folios
                        WHERE document_type_id = 61 AND folio = :folio
                        ORDER BY id DESC LIMIT 1
                        """
                    ),
                    {"folio": nc_folio},
                ).mappings().first()
                if pool:
                    folio_cls.mark_folio_used(
                        int(pool["id"]),
                        dte_id=int(nc.id),
                        branch_office_id=ref.branch_office_id,
                    )

                # 4) Esperar un poco y leer estado SF
                time.sleep(2)
                token, _ = ticket._v2_bearer_token()
                final = sf_nc_status(token, nc_folio)
                print("final", final)

                results.append(
                    {
                        "folio": nc_folio,
                        "status": emit.get("status"),
                        "message": emit.get("message"),
                        "sf_final": final,
                        "ref": f"{ref_type}/{ref.folio}",
                    }
                )
                time.sleep(3)
            except Exception as exc:
                print("ERROR folio", nc_folio, exc)
                results.append({"folio": nc_folio, "status": "error", "message": str(exc)})
                try:
                    db.rollback()
                except Exception:
                    pass
                token, _ = ticket._v2_bearer_token()
                time.sleep(2)

        print("\n=== RESUMEN ===")
        for row in results:
            print(row)
    finally:
        db.close()


if __name__ == "__main__":
    main()
