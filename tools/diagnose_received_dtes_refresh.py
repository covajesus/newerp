"""Diagnostica refresh de DTE recibidos: LibreDTE vs BD (folios en 0 / faltantes)."""
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


def main() -> int:
    since = (datetime.now() - timedelta(days=89)).strftime("%Y-%m-%d")
    until = datetime.now().strftime("%Y-%m-%d")
    url = (
        f"https://libredte.cl/api/dte/dte_recibidos/buscar/76063822"
        f"?fecha_desde={since}&fecha_hasta={until}"
    )
    print(f"Rango LibreDTE: {since} -> {until}", flush=True)
    r = requests.get(
        url,
        json={"fecha_desde": since, "fecha_hasta": until, "dte": [33, 34, 39, 61]},
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        timeout=60,
    )
    print(f"HTTP {r.status_code}", flush=True)
    data = r.json()
    if not isinstance(data, list):
        print("Respuesta inesperada:", type(data), str(data)[:500], flush=True)
        return 1

    print(f"Items LibreDTE: {len(data)}", flush=True)
    lib = []
    for item in data:
        if item.get("dte") not in [33, 34, 39, 61]:
            continue
        lib.append(
            {
                "folio": int(item.get("folio") or 0),
                "rut": rut_from_emisor(item["emisor"]),
                "dte": int(item.get("dte")),
                "total": int(item.get("total") or 0),
                "fecha": item.get("fecha"),
                "razon": item.get("razon_social"),
            }
        )
    print(f"Filtrados 33/34/39/61: {len(lib)}", flush=True)
    print(f"Con folio 0 en API: {sum(1 for x in lib if x['folio'] == 0)}", flush=True)

    db = SessionLocal()
    print("Cargando BD...", flush=True)
    zeros = db.execute(
        text(
            """
            SELECT id, folio, rut, dte_type_id, total, DATE(added_date) AS fecha
            FROM dtes
            WHERE dte_version_id = 2 AND (folio IS NULL OR folio = 0)
            ORDER BY id DESC
            """
        )
    ).fetchall()
    all_recv = db.execute(
        text(
            """
            SELECT id, folio, rut, dte_type_id, total, DATE(added_date) AS fecha
            FROM dtes
            WHERE dte_version_id = 2 AND added_date >= :since
            """
        ),
        {"since": since},
    ).fetchall()
    print(f"BD folio=0: {len(zeros)} | recibidos desde {since}: {len(all_recv)}", flush=True)

    by_key = {}
    for row in all_recv:
        key = (int(row[1] or 0), str(row[2]), int(row[3]))
        by_key.setdefault(key, []).append(row)

    by_rut_total_dte = {}
    for x in lib:
        by_rut_total_dte.setdefault((x["rut"], x["total"], x["dte"]), []).append(x)

    matched = 0
    unmatched = []
    for z in zeros:
        zid, _zf, zrut, zdte, ztotal, zfecha = z
        hits = by_rut_total_dte.get((zrut, int(ztotal or 0), int(zdte)), [])
        exact = [h for h in hits if h["fecha"] == str(zfecha)]
        use = exact or hits
        if use:
            matched += 1
            if matched <= 12:
                print(
                    f"  MATCH id={zid} rut={zrut} total={ztotal} fecha={zfecha} "
                    f"-> folio={use[0]['folio']} {use[0]['razon']}",
                    flush=True,
                )
        else:
            unmatched.append(z)
    print(f"matched={matched} unmatched={len(unmatched)}", flush=True)

    already = 0
    missing = []
    for x in lib:
        key = (x["folio"], x["rut"], x["dte"])
        if by_key.get(key):
            already += 1
        else:
            missing.append(x)
    print(f"LibreDTE ya en BD con folio correcto: {already}", flush=True)
    print(f"LibreDTE faltantes (o solo folio 0): {len(missing)}", flush=True)
    for m in missing[:25]:
        print(" ", m, flush=True)

    print("\n=== fechas added_date de folio=0 ===", flush=True)
    for row in db.execute(
        text(
            """
            SELECT DATE(added_date), COUNT(*) FROM dtes
            WHERE dte_version_id = 2 AND (folio = 0 OR folio IS NULL)
            GROUP BY DATE(added_date) ORDER BY 1 DESC LIMIT 20
            """
        )
    ).fetchall():
        print(row, flush=True)

    # POST vs GET count
    print("\n=== POST vs GET ===", flush=True)
    resp_post = requests.post(
        "https://libredte.cl/api/dte/dte_recibidos/buscar/76063822",
        json={"fecha_desde": since, "fecha_hasta": until, "dte": [33, 34, 39, 61]},
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        timeout=60,
    )
    post_data = resp_post.json()
    print(
        f"POST HTTP {resp_post.status_code} -> "
        f"{len(post_data) if isinstance(post_data, list) else post_data}",
        flush=True,
    )

    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
