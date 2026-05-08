from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.backend.db.models import CapitulationBankAccountModel


class CapitulationBankAccountClass:
    def __init__(self, db: Session):
        self.db = db

    def store(self, form_data, user_id=None):
        payload = {
            "bank_id": getattr(form_data, "bank_id", None),
            "account_type_id": getattr(form_data, "account_type_id", None),
            "account_number": getattr(form_data, "account_number", None),
            "identification_number": getattr(form_data, "identification_number", None),
            "email": getattr(form_data, "email", None),
        }

        has_any_bank_data = any(v not in (None, "", "null", "undefined") for v in payload.values())
        if not has_any_bank_data:
            return {"status": "skipped", "message": "Sin datos bancarios para guardar"}

        missing_fields = [k for k, v in payload.items() if v in (None, "", "null", "undefined")]
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Faltan datos bancarios obligatorios: {', '.join(missing_fields)}",
            )

        identification_number = str(payload["identification_number"]).strip()
        if not identification_number:
            raise HTTPException(status_code=400, detail="identification_number inválido")

        try:
            account_number = int(str(payload["account_number"]).strip())
        except ValueError:
            raise HTTPException(status_code=400, detail="El número de cuenta debe ser numérico")

        bank_account = None
        if user_id is not None:
            bank_account = (
                self.db.query(CapitulationBankAccountModel)
                .filter(CapitulationBankAccountModel.user_id == int(user_id))
                .first()
            )
        if not bank_account:
            bank_account = (
                self.db.query(CapitulationBankAccountModel)
                .filter(CapitulationBankAccountModel.identification_number == identification_number)
                .first()
            )

        if not bank_account:
            bank_account = CapitulationBankAccountModel()
            bank_account.identification_number = identification_number
            bank_account.added_date = datetime.now()
            self.db.add(bank_account)

        bank_account.user_id = int(user_id) if user_id is not None else bank_account.user_id
        bank_account.bank_id = int(payload["bank_id"])
        bank_account.account_type_id = int(payload["account_type_id"])
        bank_account.account_number = account_number
        bank_account.email = str(payload["email"]).strip()
        bank_account.updated_date = datetime.now()

        try:
            self.db.commit()
            return {"status": "success", "message": "Datos bancarios guardados", "id": bank_account.id}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error guardando datos bancarios: {str(e)}")
