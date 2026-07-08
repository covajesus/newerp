"""Inspecciona un folio y sus datos de pago (dtes_payment_data)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import bindparam, text

from app.backend.db.database import SessionLocal

FOLIO = int(sys.argv[1]) if len(sys.argv) > 1 else 32130511


def main() -> int:
    db = SessionLocal()

    print(f"=== DTE folio={FOLIO} ===")
    rows = db.execute(
        text(
            """
            SELECT id, folio, dte_version_id, dte_type_id, status_id, payment_type_id,
                   cash_amount, card_amount, total, comment, payment_comment,
                   added_date, updated_date
            FROM dtes
            WHERE folio = :folio
            ORDER BY id
            """
        ),
        {"folio": FOLIO},
    ).fetchall()

    if not rows:
        print("  (no existe DTE con ese folio)")
    for r in rows:
        cols = ["id","folio","dte_version_id","dte_type_id","status_id","payment_type_id",
                "cash_amount","card_amount","total","comment","payment_comment","added_date","updated_date"]
        print("  " + " | ".join(f"{c}={v}" for c, v in zip(cols, r)))

    dte_ids = [r[0] for r in rows]

    print("\n=== dtes_payment_data (por folio y por dte_id) ===")
    conds = ["folio = :folio"]
    params: dict = {"folio": FOLIO}
    stmt = text(
        """
        SELECT id, dte_id, folio, order_id, reference_id, payment_status,
               approval_code, payment_type_id, amount, rut, added_date, updated_date, raw_payload
        FROM dtes_payment_data
        WHERE folio = :folio OR dte_id IN :ids
        ORDER BY id
        """
    ).bindparams(bindparam("ids", expanding=True))
    pd = db.execute(stmt, {"folio": FOLIO, "ids": dte_ids or [-1]}).fetchall()

    if not pd:
        print("  (sin registros de pago para este folio)")
    for r in pd:
        cols = ["id","dte_id","folio","order_id","reference_id","payment_status","approval_code",
                "payment_type_id","amount","rut","added_date","updated_date","raw_payload"]
        for c, v in zip(cols, r):
            sv = str(v)
            if c == "raw_payload" and len(sv) > 2000:
                sv = sv[:2000] + "...(truncado)"
            print(f"  {c} = {sv}")
        print("  ---")

    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
