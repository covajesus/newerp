"""
Backfill de pagos Klap para DTEs pagados del periodo 2026-07 (dte_version_id=1).

Para cada DTE con period='2026-07', status_id=5, dte_version_id=1 que tenga una
orden Klap 'completed' asociada por folio, toma el approval_code de la orden y:
  - comment            = "Código de autorización: {approval_code}"
  - payment_type_id    = 2
  - si cash_amount > 0 -> card_amount = cash_amount, cash_amount = 0

Por defecto corre en DRY-RUN (no escribe). Para aplicar:  python tools/fix_klap_paid_comments_2026_07.py --commit
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.backend.db.database import SessionLocal

PERIOD = "2026-07"
DTE_VERSION_ID = 1


def approval_code_from_payload(raw_payload: str | None) -> str | None:
    if not raw_payload:
        return None
    try:
        payload = json.loads(raw_payload)
    except (ValueError, TypeError):
        return None
    gateway = payload.get("gateway") if isinstance(payload, dict) else None
    if not isinstance(gateway, dict):
        return None
    details = gateway.get("payment_details")
    if not isinstance(details, list):
        return None
    for item in details:
        if isinstance(item, dict) and item.get("key") == "approval_code":
            value = str(item.get("value") or "").strip()
            return value or None
    return None


def main() -> int:
    commit = "--commit" in sys.argv
    db = SessionLocal()

    dtes = db.execute(
        text(
            """
            SELECT id, folio, cash_amount, card_amount, total, payment_type_id, comment
            FROM dtes
            WHERE period = :period AND status_id = 5 AND dte_version_id = :ver
            ORDER BY id DESC
            """
        ),
        {"period": PERIOD, "ver": DTE_VERSION_ID},
    ).fetchall()

    planned = []
    no_code = 0

    for dte in dtes:
        dte_id, folio, cash_amount, card_amount, total, payment_type_id, comment = dte

        pay_row = db.execute(
            text(
                """
                SELECT raw_payload
                FROM dtes_payment_data
                WHERE folio = :folio AND payment_status = 'completed'
                ORDER BY id DESC
                LIMIT 1
                """
            ),
            {"folio": folio},
        ).fetchone()

        approval_code = approval_code_from_payload(pay_row[0]) if pay_row else None
        if not approval_code:
            no_code += 1
            continue

        new_comment = f"Código de autorización: {approval_code}"
        cash = int(cash_amount or 0)
        card = int(card_amount or 0)
        if cash > 0:
            new_card = cash
            new_cash = 0
        else:
            new_card = card
            new_cash = cash

        planned.append(
            {
                "id": dte_id,
                "folio": folio,
                "approval_code": approval_code,
                "old_comment": comment,
                "new_comment": new_comment,
                "cash": cash,
                "card": card,
                "new_cash": new_cash,
                "new_card": new_card,
                "old_ptype": payment_type_id,
            }
        )

    print(f"Periodo {PERIOD} | tipo (dte_version_id)={DTE_VERSION_ID} | status_id=5")
    print(f"DTEs revisados: {len(dtes)}")
    print(f"Con orden Klap 'completed' + approval_code: {len(planned)}")
    print(f"Sin approval_code (se omiten): {no_code}")
    moved = sum(1 for p in planned if p['new_cash'] != p['cash'])
    print(f"De esos, con cash -> card a mover: {moved}")
    print("--- muestra (primeros 12) ---")
    for p in planned[:12]:
        print(
            f"  folio={p['folio']} code={p['approval_code']} "
            f"cash {p['cash']}->{p['new_cash']} card {p['card']}->{p['new_card']} "
            f"ptype {p['old_ptype']}->2 | comment='{p['new_comment']}'"
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
                SET comment = :comment,
                    payment_type_id = 2,
                    card_amount = :card,
                    cash_amount = :cash
                WHERE id = :id
                """
            ),
            {
                "comment": p["new_comment"],
                "card": p["new_card"],
                "cash": p["new_cash"],
                "id": p["id"],
            },
        )
        updated += 1

    db.commit()
    print(f"\nCOMMIT OK: {updated} DTEs actualizados.")
    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
