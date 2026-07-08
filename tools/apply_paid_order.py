"""Aplica el pago real de Klap a un folio usando record_payment_return sobre una orden concreta.

Uso:  python tools/apply_paid_order.py <reference_id> <order_id>
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.backend.classes.dte_payment_data_class import DtePaymentDataClass
from app.backend.db.database import SessionLocal

REFERENCE_ID = sys.argv[1] if len(sys.argv) > 1 else "32130511"
ORDER_ID = sys.argv[2] if len(sys.argv) > 2 else "3507M9a08c1002b524347b79ec635a1f3b224"


def main() -> int:
    db = SessionLocal()
    result = DtePaymentDataClass(db).record_payment_return(
        REFERENCE_ID,
        ORDER_ID,
        source="manual_fix_apply_paid_order",
    )
    print("dte_updated:", result.get("dte_updated"))
    pd = result.get("payment_data") or {}
    for k in ("payment_status", "approval_code", "amount", "payment_type_id", "folio"):
        print(f"  {k} = {pd.get(k)}")
    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
