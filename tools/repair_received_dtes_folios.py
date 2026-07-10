"""
Repara DTEs recibidos (dte_version_id=2):
  - Corrige folio=0 con el folio real de LibreDTE
  - Elimina duplicados folio=0 cuando ya existe el folio correcto
  - Inserta los faltantes

Uso: python tools/repair_received_dtes_folios.py [--commit]
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.backend.classes.helper_class import HelperClass
from app.backend.db.database import SessionLocal

TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"


def rut_from_emisor(emisor) -> str:
    e = int(emisor)
    body = str(e)
    if e < 10000000:
        body = "0" + body
    dv = HelperClass.verificator_digit(body)
    return f"{body}-{dv}"


def fetch_libredte() -> list[dict]:
    since = (datetime.now() - timedelta(days=89)).strftime("%Y-%m-%d")
    until = datetime.now().strftime("%Y-%m-%d")
    url = (
        f"https://libredte.cl/api/dte/dte_recibidos/buscar/76063822"
        f"?fecha_desde={since}&fecha_hasta={until}"
    )
    print(f"LibreDTE {since} -> {until}", flush=True)
    r = requests.get(
        url,
        json={"fecha_desde": since, "fecha_hasta": until, "dte": [33, 34, 39, 61]},
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        raise RuntimeError(f"Respuesta inesperada: {data}")
    out = []
    for item in data:
        if item.get("dte") not in [33, 34, 39, 61]:
            continue
        folio = int(item.get("folio") or 0)
        if folio <= 0:
            continue
        total = item["total"] if item["total"] is not None else 0
        net = item["neto"] if item["neto"] is not None else 0
        if item["dte"] == 61:
            total = -abs(total)
            net = -abs(net)
        out.append(
            {
                "folio": folio,
                "rut": rut_from_emisor(item["emisor"]),
                "dte": int(item["dte"]),
                "total": int(total),
                "net": int(net),
                "fecha": str(item.get("fecha") or ""),
                "razon": (item.get("razon_social") or "").upper(),
            }
        )
    print(f"LibreDTE validos: {len(out)}", flush=True)
    return out


def main() -> int:
    commit = "--commit" in sys.argv
    lib = fetch_libredte()
    db = SessionLocal()

    since = (datetime.now() - timedelta(days=89)).strftime("%Y-%m-%d")
    rows = db.execute(
        text(
            """
            SELECT id, folio, rut, dte_type_id, total, DATE(added_date) AS fecha
            FROM dtes
            WHERE dte_version_id = 2 AND added_date >= :since
            """
        ),
        {"since": since},
    ).fetchall()
    zeros = db.execute(
        text(
            """
            SELECT id, folio, rut, dte_type_id, total, DATE(added_date) AS fecha
            FROM dtes
            WHERE dte_version_id = 2 AND (folio IS NULL OR folio = 0)
            """
        )
    ).fetchall()

    by_correct = {}
    for r in rows:
        key = (int(r[1] or 0), str(r[2]), int(r[3]))
        if key[0] > 0:
            by_correct[key] = r

    updates = []  # (id, folio, net, total)
    deletes = []  # id
    inserts = []

    used_zero_ids = set()
    for x in lib:
        key = (x["folio"], x["rut"], x["dte"])
        if key in by_correct:
            # borrar huérfanos folio=0 del mismo doc (mismo rut/tipo/total; fecha puede diferir 1 día)
            for z in zeros:
                if z[0] in used_zero_ids:
                    continue
                if str(z[2]) != x["rut"] or int(z[3]) != x["dte"] or int(z[4] or 0) != x["total"]:
                    continue
                deletes.append(z[0])
                used_zero_ids.add(z[0])
            continue

        # buscar folio=0 para actualizar (preferir misma fecha; si no, cualquier match rut/tipo/total)
        candidate = None
        fallback = None
        for z in zeros:
            if z[0] in used_zero_ids:
                continue
            if str(z[2]) != x["rut"] or int(z[3]) != x["dte"] or int(z[4] or 0) != x["total"]:
                continue
            zfecha = str(z[5]) if z[5] else ""
            if x["fecha"] and zfecha and zfecha == x["fecha"]:
                candidate = z
                break
            if fallback is None:
                fallback = z
        candidate = candidate or fallback
        if candidate:
            updates.append((candidate[0], x["folio"], x["net"], x["total"]))
            used_zero_ids.add(candidate[0])
        else:
            inserts.append(x)

    # zeros no usados quedan como están (no matchearon LibreDTE)
    leftover_zeros = [z for z in zeros if z[0] not in used_zero_ids]

    print(f"Plan: update={len(updates)} delete_dupes={len(deletes)} insert={len(inserts)} leftover_folio0={len(leftover_zeros)}", flush=True)
    for u in updates[:5]:
        print(f"  UPDATE id={u[0]} -> folio={u[1]}", flush=True)
    for d in deletes[:5]:
        print(f"  DELETE id={d}", flush=True)
    for i in inserts[:5]:
        print(f"  INSERT folio={i['folio']} rut={i['rut']} total={i['total']}", flush=True)

    if not commit:
        print("\nDRY-RUN. Ejecuta con --commit para aplicar.", flush=True)
        db.close()
        return 0

    for dte_id, folio, net, total in updates:
        db.execute(
            text(
                """
                UPDATE dtes
                SET folio = :folio,
                    subtotal = COALESCE(subtotal, :net),
                    tax = COALESCE(tax, :tax)
                WHERE id = :id
                """
            ),
            {"folio": folio, "net": net, "tax": int(total) - int(net), "id": dte_id},
        )

    if deletes:
        db.execute(
            text("DELETE FROM dtes WHERE id IN :ids").bindparams(
                __import__("sqlalchemy").bindparam("ids", expanding=True)
            ),
            {"ids": deletes},
        )

    # asegurar proveedores
    existing_ruts = {
        r[0]
        for r in db.execute(text("SELECT rut FROM suppliers")).fetchall()
    }
    for x in inserts:
        if x["rut"] not in existing_ruts:
            db.execute(
                text("INSERT INTO suppliers (rut, supplier) VALUES (:rut, :supplier)"),
                {"rut": x["rut"], "supplier": x["razon"] or x["rut"]},
            )
            existing_ruts.add(x["rut"])
        db.execute(
            text(
                """
                INSERT INTO dtes (
                    branch_office_id, cashier_id, dte_type_id, dte_version_id,
                    status_id, chip_id, rut, folio, cash_amount, card_amount,
                    subtotal, tax, discount, total, added_date
                ) VALUES (
                    0, 0, :dte, 2,
                    1, 0, :rut, :folio, :total, 0,
                    :net, :tax, 0, :total, :added
                )
                """
            ),
            {
                "dte": x["dte"],
                "rut": x["rut"],
                "folio": x["folio"],
                "total": x["total"],
                "net": x["net"],
                "tax": int(x["total"]) - int(x["net"]),
                "added": (x["fecha"] + " 00:00:00") if x["fecha"] else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

    db.commit()
    after0 = db.execute(
        text("SELECT COUNT(*) FROM dtes WHERE dte_version_id=2 AND (folio=0 OR folio IS NULL)")
    ).scalar()
    print(f"\nCOMMIT OK. folio=0 restantes: {after0}", flush=True)
    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
