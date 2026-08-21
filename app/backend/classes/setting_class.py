from app.backend.db.models import SettingModel
from sqlalchemy.orm import Session


class SettingClass:
    def __init__(self, db):
        self.db = db

    def get(self):
        try:
            data_query = self.db.query(
                SettingModel.id,
                SettingModel.capitulation_open_period,
                SettingModel.capitulation_close_period,
                SettingModel.honorary_open_period,
                SettingModel.honorary_close_period,
                SettingModel.dropbox_token,
                SettingModel.facebook_token,
                SettingModel.simplefactura_token,
                SettingModel.caf_limit,
                SettingModel.percentage_honorary_bill,
                SettingModel.apigetaway_token,
                SettingModel.accounting_backend,
                SettingModel.sii_login_rut,
                SettingModel.sii_tax_password,
            ).filter(SettingModel.id == 1).first()

            if data_query:
                tax_password = (data_query.sii_tax_password or "").strip()
                setting_data = {
                    "id": data_query.id,
                    "capitulation_open_period": data_query.capitulation_open_period,
                    "capitulation_close_period": data_query.capitulation_close_period,
                    "honorary_open_period": data_query.honorary_open_period,
                    "honorary_close_period": data_query.honorary_close_period,
                    "dropbox_token": data_query.dropbox_token,
                    "facebook_token": data_query.facebook_token,
                    "simplefactura_token": data_query.simplefactura_token,
                    "caf_limit": data_query.caf_limit,
                    "percentage_honorary_bill": data_query.percentage_honorary_bill,
                    "apigetaway_token": data_query.apigetaway_token,
                    "accounting_backend": int(data_query.accounting_backend or 1),
                    "sii_login_rut": data_query.sii_login_rut or "",
                    "sii_tax_password_configured": bool(tax_password),
                    # Never return the plain password on GET
                    "sii_tax_password": "",
                }

                return {"setting_data": setting_data}

            else:
                return {"error": "No se encontraron datos para el campo especificado."}

        except Exception as e:
            return {"error": str(e)}

    def get_sii_credentials(self) -> dict:
        """Internal: RUT + tax password for BTE emission (not exposed via public GET)."""
        row = self.db.query(SettingModel).filter(SettingModel.id == 1).first()
        if not row:
            return {"login_rut": "", "password": ""}
        return {
            "login_rut": (row.sii_login_rut or "").strip(),
            "password": (row.sii_tax_password or "").strip(),
        }

    def update(self, form_data):
        settings = self.db.query(SettingModel).filter(SettingModel.id == 1).first()

        settings.capitulation_open_period = form_data.capitulation_open_period
        settings.capitulation_close_period = form_data.capitulation_close_period
        settings.honorary_open_period = form_data.honorary_open_period
        settings.honorary_close_period = form_data.honorary_close_period
        settings.dropbox_token = form_data.dropbox_token
        settings.facebook_token = form_data.facebook_token
        settings.simplefactura_token = form_data.simplefactura_token
        settings.caf_limit = form_data.caf_limit
        settings.percentage_honorary_bill = form_data.percentage_honorary_bill
        settings.apigetaway_token = form_data.apigetaway_token
        try:
            settings.accounting_backend = int(getattr(form_data, "accounting_backend", 1) or 1)
        except (TypeError, ValueError):
            settings.accounting_backend = 1
        if settings.accounting_backend not in (1, 2):
            settings.accounting_backend = 1

        login_rut = getattr(form_data, "sii_login_rut", None)
        if login_rut is not None:
            settings.sii_login_rut = str(login_rut).strip() or None

        new_password = getattr(form_data, "sii_tax_password", None)
        if new_password is not None and str(new_password).strip():
            settings.sii_tax_password = str(new_password).strip()

        self.db.commit()

        return settings

    def test_sii_tax_password(self, login_rut: str | None = None, password: str | None = None) -> dict:
        try:
            from app.backend.classes.sii.bte import validate_login
        except ModuleNotFoundError as e:
            return {
                "status": "error",
                "message": f"Missing dependency for SII BTE: {e}. Install httpx in the service venv.",
            }

        creds = self.get_sii_credentials()
        rut = (login_rut or creds["login_rut"] or "").strip()
        tax_password = (password or creds["password"] or "").strip()
        if not rut or not tax_password:
            return {
                "status": "error",
                "message": "Missing SII login RUT or tax password in settings",
            }
        try:
            ok = validate_login(rut=rut, password=tax_password)
            if ok:
                return {"status": "success", "message": "SII connection OK (tax password valid)"}
            return {"status": "error", "message": "Could not authenticate with SII"}
        except Exception as e:
            return {"status": "error", "message": f"Error testing SII tax password: {e}"}

    def update_token(self, access_token):
        settings = self.db.query(SettingModel).filter(SettingModel.id == 1).first()

        settings.simplefactura_token = access_token

        self.db.commit()

        return settings
