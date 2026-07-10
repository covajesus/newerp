"""
Backfill chip $5.000 en DTEs emitidos (dte_version_id=1) de 2026-06 y 2026-07.

Para cada DTE con chip_id=1 (y category_id != 3):
  - Suma 5000 a card_amount si card>0, si no a cash_amount
  - Recalcula subtotal / tax
  - Deja total = monto bruto (cash o card) con el chip incluido

DRY-RUN por defecto. Aplicar: python tools/backfill_chip_amounts_2026_06_07.py --commit
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.backend.db.database import SessionLocal

CHIP = 5000
PERIODS = ["2026-06", "2026-07"]


def main() -> int:
    commit = "--commit" in sys.argv
    db = SessionLocal()

    rows = db.execute(
        text(
            """
            SELECT id, folio, period, dte_type_id, status_id, category_id,
                   cash_amount, card_amount, total, subtotal, tax
            FROM dtes
            WHERE dte_version_id = 1
              AND chip_id = 1
              AND period IN :periods
              AND (category_id IS NULL OR category_id <> 3)
            ORDER BY period, id
            """
        ).bindparams(__import__("sqlalchemy").bindparam("periods", expanding=True)),
        {"periods": PERIODS},
    ).fetchall()

    planned = []
    for r in rows:
        (dte_id, folio, period, dtype, status, cat, cash, card, total, sub, tax) = r
        cash = int(cash or 0)
        card = int(card or 0)
        total = int(total or 0)

        # Si cash y card son iguales, es el mismo monto duplicado → tratar como cash.
        if card > 0 and cash > 0 and card == cash:
            card = 0

        if card > 0 and cash == 0:
            new_card = card + CHIP
            new_cash = 0
            new_total = new_card
        elif cash > 0:
            new_cash = cash + CHIP
            new_card = card
            new_total = new_cash
        else:
            new_cash = total + CHIP
            new_card = 0
            new_total = new_cash

        new_sub = round(new_total / 1.19)
        new_tax = new_total - new_sub
        planned.append(
            {
                "id": dte_id,
                "folio": folio,
                "period": period,
                "cash": cash,
                "card": card,
                "total": total,
                "new_cash": new_cash,
                "new_card": new_card,
                "new_total": new_total,
                "new_sub": new_sub,
                "new_tax": new_tax,
            }
        )

    print(f"Candidatos: {len(planned)}")
    for p in planned[:15]:
        print(
            f"  id={p['id']} folio={p['folio']} {p['period']} "
            f"cash {p['cash']}->{p['new_cash']} card {p['card']}->{p['new_card']} "
            f"total {p['total']}->{p['new_total']}"
        )
    if len(planned) > 15:
        print(f"  ... y {len(planned) - 15} mas")

    if not commit:
        print("\nDRY-RUN. Ejecuta con --commit para aplicar.")
        db.close()
        return 0

    for p in planned:
        db.execute(
            text(
                """
                UPDATE dtes
                SET cash_amount = :cash,
                    card_amount = :card,
                    total = :total,
                    subtotal = :sub,
                    tax = :tax
                WHERE id = :id
                """
            ),
            {
                "cash": p["new_cash"],
                "card": p["new_card"],
                "total": p["new_total"],
                "sub": p["new_sub"],
                "tax": p["new_tax"],
                "id": p["id"],
            },
        )
    db.commit()
    print(f"\nCOMMIT OK: {len(planned)} DTEs actualizados (+{CHIP} chip).")
    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
