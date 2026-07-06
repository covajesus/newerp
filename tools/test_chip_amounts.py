"""Verifica montos estacionamiento vs chip (sin inferir chip desde el monto)."""
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.backend.classes.customer_ticket_class import (
    _apply_ticket_draft_amounts,
    document_gross_from_form,
    parking_gross_from_form,
    ticket_payment_total,
)


class FormData:
    def __init__(self, amount: int, chip_id: int, category_id: int = 1):
        self.amount = amount
        self.chip_id = chip_id
        self.category_id = category_id


def make_dte():
    return SimpleNamespace(
        chip_id=0,
        category_id=1,
        total=0,
        cash_amount=0,
        subtotal=0,
        tax=0,
        discount=0,
        card_amount=0,
    )


def run_case(label: str, amount: int, chip_id: int, expected_parking: int, expected_pay: int):
    form = FormData(amount, chip_id)
    dte = make_dte()
    _apply_ticket_draft_amounts(dte, form)

    parking = parking_gross_from_form(form)
    doc_gross = document_gross_from_form(form)
    pay = ticket_payment_total(dte)

    ok = (
        parking == expected_parking
        and doc_gross == expected_pay
        and dte.total == expected_parking
        and dte.cash_amount == expected_pay
        and pay == expected_pay
    )
    status = "OK" if ok else "FAIL"
    print(
        f"[{status}] {label}: "
        f"form.amount={amount} chip_id={chip_id} -> "
        f"parking={parking} doc={doc_gross} dte.total={dte.total} "
        f"cash_amount={dte.cash_amount} pago={pay} "
        f"(esperado parking={expected_parking} pago={expected_pay})"
    )
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    run_case("Est. $70.000 + chip", 70000, 1, 70000, 75000)
    run_case("Est. $75.000 + chip", 75000, 1, 75000, 80000)
    run_case("Est. $75.000 sin chip", 75000, 0, 75000, 75000)
    run_case("Est. $70.000 sin chip", 70000, 0, 70000, 70000)
    print("\nTodos los casos pasaron.")
