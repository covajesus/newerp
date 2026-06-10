"""Prueba send_v2_invoice para un folio emitido v2."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.backend.db.database import SessionLocal
from app.backend.db.models import DteModel, CustomerModel
from app.backend.classes.whatsapp_class import WhatsappClass


def main():
    folio = int(sys.argv[1]) if len(sys.argv) > 1 else 32130034
    db = SessionLocal()
    try:
        dte = (
            db.query(DteModel)
            .filter(DteModel.folio == folio)
            .order_by(DteModel.id.desc())
            .first()
        )
        if not dte:
            print(json.dumps({"status": "error", "message": f"No hay DTE con folio {folio}"}, ensure_ascii=False))
            return 1

        customer = db.query(CustomerModel).filter(CustomerModel.rut == dte.rut).first()
        print(
            json.dumps(
                {
                    "dte_id": dte.id,
                    "folio": dte.folio,
                    "rut": dte.rut,
                    "dte_type_id": dte.dte_type_id,
                    "dte_version_id": dte.dte_version_id,
                    "status_id": dte.status_id,
                    "total": dte.total,
                    "phone": getattr(customer, "phone", None) if customer else None,
                },
                ensure_ascii=False,
                indent=2,
            ),
            flush=True,
        )

        result = WhatsappClass(db).send_v2_invoice(dte, dte.rut)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0 if result.get("status") == "success" else 2
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
