"""Consulta directa a Klap/Multicaja el estado de las órdenes y transacciones de un folio."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.backend.classes.payment_gateway_class import PaymentGatewayClass
from app.backend.db.database import SessionLocal

FOLIO = int(sys.argv[1]) if len(sys.argv) > 1 else 32130511


def dump(label: str, data) -> None:
    print(f"\n----- {label} -----")
    try:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except TypeError:
        print(data)


def main() -> int:
    db = SessionLocal()
    gw = PaymentGatewayClass()
    print(f"API base: {gw.base_url} | api_key set: {bool(gw.api_key)}")

    rows = db.execute(
        text(
            """
            SELECT order_id, reference_id
            FROM dtes_payment_data
            WHERE folio = :folio
            ORDER BY id
            """
        ),
        {"folio": FOLIO},
    ).fetchall()

    print(f"Órdenes registradas para folio {FOLIO}: {[r[0] for r in rows]}")

    for order_id, ref in rows:
        try:
            order = gw.get_order(str(order_id))
            status = order.get("status") if isinstance(order, dict) else None
            print(f"\n=== order_id={order_id} (ref={ref}) -> status={status} ===")
            dump("get_order", order)
        except Exception as exc:
            print(f"\n=== order_id={order_id} ERROR: {exc}")

    seen_refs = {r[1] for r in rows if r[1]}
    seen_refs.add(str(FOLIO))
    for ref in sorted(seen_refs):
        try:
            tx = gw.list_transactions(reference_id=str(ref))
            dump(f"list_transactions reference_id={ref}", tx)
        except Exception as exc:
            print(f"\nlist_transactions ref={ref} ERROR: {exc}")

    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
