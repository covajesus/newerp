"""
Detecta (y opcionalmente corrige) DTEs con payment_type_id = 2 (Tarjeta/Klap)
que en realidad fueron pagos manuales de Depósito/Transferencia.

Criterio de "mal clasificado":
  payment_type_id = 2  Y  tiene comprobante manual (support IS NOT NULL)
  Y  NO existe una orden Klap 'completed' para ese folio
  Y  NO tiene "Código de autorización" en el comment (huella de Klap real)

Corrección propuesta:
  - payment_type_id -> 3 (Transferencia) por defecto, o 1 (Depósito) si el
    payment_number tiene formato de depósito "AA-#########".
  - Si card_amount > 0 y cash_amount = 0 -> revierte: cash_amount = card_amount, card_amount = 0.

DRY-RUN por defecto. Filtra por periodo con --period=YYYY-MM (repetible) o --all.
Aplica con --commit.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.backend.db.database import SessionLocal

DEPOSIT_NUMBER_RE = re.compile(r"^[A-Za-z]{2}-\d+$")


def parse_periods(argv: list[str]) -> list[str] | None:
    if "--all" in argv:
        return None
    periods = [a.split("=", 1)[1] for a in argv if a.startswith("--period=")]
    return periods or ["2026-07"]


def main() -> int:
    argv = sys.argv[1:]
    commit = "--commit" in argv
    periods = parse_periods(argv)

    db = SessionLocal()

    where_period = ""
    params: dict = {}
    if periods is not None:
        where_period = "AND d.period IN :periods"
        params["periods"] = periods

    sql = text(
        f"""
        SELECT d.id, d.folio, d.period, d.status_id, d.payment_type_id,
               d.cash_amount, d.card_amount, d.payment_number, d.comment,
               (SELECT COUNT(*) FROM dtes_payment_data p
                 WHERE p.folio = d.folio AND p.payment_status = 'completed') AS klap_ok
        FROM dtes d
        WHERE d.dte_version_id = 1
          AND d.payment_type_id = 2
          AND d.support IS NOT NULL
          {where_period}
        ORDER BY d.period, d.folio
        """
    )
    if periods is not None:
        sql = sql.bindparams(__import__("sqlalchemy").bindparam("periods", expanding=True))

    rows = db.execute(sql, params).fetchall()

    planned = []
    for r in rows:
        (dte_id, folio, period, status, ptype, cash, card, pnum, comment, klap_ok) = r
        if klap_ok and klap_ok > 0:
            continue  # pago Klap real, no tocar
        if comment and "Código de autorización" in str(comment):
            continue  # huella de Klap real, no tocar
        cash = int(cash or 0)
        card = int(card or 0)
        pnum_s = str(pnum or "").strip()
        new_ptype = 1 if DEPOSIT_NUMBER_RE.match(pnum_s) else 3
        # revertir montos si fueron movidos a tarjeta
        if card > 0 and cash == 0:
            new_cash, new_card = card, 0
        else:
            new_cash, new_card = cash, card
        planned.append({
            "id": dte_id, "folio": folio, "period": period, "status": status,
            "old_ptype": ptype, "new_ptype": new_ptype,
            "cash": cash, "card": card, "new_cash": new_cash, "new_card": new_card,
            "pnum": pnum_s,
        })

    print(f"Candidatos (type=2 + comprobante manual, sin Klap real): {len(planned)}")
    print(f"Periodos: {'TODOS' if periods is None else periods}")
    print("--- plan ---")
    for p in planned:
        print(
            f"  folio={p['folio']} ({p['period']}) ptype {p['old_ptype']}->{p['new_ptype']} "
            f"cash {p['cash']}->{p['new_cash']} card {p['card']}->{p['new_card']} num='{p['pnum']}'"
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
                SET payment_type_id = :ptype,
                    cash_amount = :cash,
                    card_amount = :card
                WHERE id = :id
                """
            ),
            {"ptype": p["new_ptype"], "cash": p["new_cash"], "card": p["new_card"], "id": p["id"]},
        )
        updated += 1

    db.commit()
    print(f"\nCOMMIT OK: {updated} folios corregidos.")
    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
