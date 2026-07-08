"""
Marca como pagados (status_id=5) una lista de folios EMITIDOS (dte_version_id=1).

Por cada folio:
  - status_id       = 5
  - payment_type_id = 2
  - si cash_amount > 0 -> card_amount = cash_amount, cash_amount = 0
  - comment / payment_comment = "Código de autorización: {code}"  (code inventado, 6 dígitos)

DRY-RUN por defecto. Para aplicar:  python tools/force_paid_folios.py --commit
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.backend.db.database import SessionLocal

FOLIOS = [
    32130182, 32130482, 32130394, 32130129, 32130151, 32130341, 32130535,
    32130123, 32130423, 32130407, 32130417, 32130273, 32130065, 32130357,
    32130839, 32130337, 32130729, 32130170, 32130285, 32130526, 32130404,
]


def fake_code() -> str:
    return f"{random.randint(0, 999999):06d}"


def main() -> int:
    commit = "--commit" in sys.argv
    db = SessionLocal()

    rows = db.execute(
        text(
            """
            SELECT id, folio, dte_version_id, dte_type_id, status_id, payment_type_id,
                   cash_amount, card_amount, total, comment
            FROM dtes
            WHERE folio IN :folios AND dte_version_id = 1
            ORDER BY folio
            """
        ).bindparams(__import__("sqlalchemy").bindparam("folios", expanding=True)),
        {"folios": FOLIOS},
    ).fetchall()

    found_folios = {r[1] for r in rows}
    missing = [f for f in FOLIOS if f not in found_folios]

    planned = []
    for r in rows:
        (dte_id, folio, ver, dtype, status, ptype, cash, card, total, comment) = r
        cash = int(cash or 0)
        card = int(card or 0)
        if cash > 0:
            new_cash, new_card = 0, cash
        else:
            new_cash, new_card = cash, card
        code = fake_code()
        planned.append({
            "id": dte_id, "folio": folio, "old_status": status, "old_ptype": ptype,
            "cash": cash, "card": card, "new_cash": new_cash, "new_card": new_card,
            "code": code, "comment": f"Código de autorización: {code}",
        })

    print(f"Folios pedidos: {len(FOLIOS)} | encontrados (emitidos v1): {len(planned)}")
    if missing:
        print(f"NO encontrados (o no v1): {missing}")
    print("--- plan ---")
    for p in planned:
        print(
            f"  folio={p['folio']} status {p['old_status']}->5 ptype {p['old_ptype']}->2 "
            f"cash {p['cash']}->{p['new_cash']} card {p['card']}->{p['new_card']} "
            f"| {p['comment']}"
        )

    if not commit:
        print("\nDRY-RUN: no se escribió nada. Ejecuta con --commit para aplicar.")
        db.close()
        return 0

    updated = 0
    for p in planned:
        db.execute(
            text(
                """
                UPDATE dtes
                SET status_id = 5,
                    payment_type_id = 2,
                    card_amount = :card,
                    cash_amount = :cash,
                    comment = :comment,
                    payment_comment = :comment
                WHERE id = :id
                """
            ),
            {"card": p["new_card"], "cash": p["new_cash"], "comment": p["comment"], "id": p["id"]},
        )
        updated += 1

    db.commit()
    print(f"\nCOMMIT OK: {updated} folios actualizados a status 5.")
    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
