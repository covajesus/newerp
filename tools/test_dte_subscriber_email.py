"""Prueba envío correo HTML + PDF + enlace Klap para un folio."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from app.backend.classes.dte_subscriber_email_class import DteSubscriberEmailClass
from app.backend.db.database import SessionLocal
from app.backend.db.models import CustomerModel, DteModel

FOLIO = int(sys.argv[1]) if len(sys.argv) > 1 else 32130850
TO_EMAIL = sys.argv[2] if len(sys.argv) > 2 else "jesusrafaelcovahuerta@gmail.com"


def main() -> None:
    db = SessionLocal()
    try:
        dte = (
            db.query(DteModel)
            .filter(DteModel.folio == FOLIO)
            .order_by(DteModel.id.desc())
            .first()
        )
        if not dte:
            print(json.dumps({"status": "error", "message": f"DTE folio {FOLIO} no encontrado"}, indent=2))
            sys.exit(1)

        customer = None
        if dte.rut:
            customer = db.query(CustomerModel).filter(CustomerModel.rut == dte.rut).first()

        print(
            f"Enviando folio={FOLIO} tipo={dte.dte_type_id} total={dte.total} "
            f"to={TO_EMAIL} rut={dte.rut}",
            flush=True,
        )
        result = DteSubscriberEmailClass(db).send(dte, customer=customer, to_emails=TO_EMAIL)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result.get("status") != "success":
            sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
