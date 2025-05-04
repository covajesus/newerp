from app.backend.db.models import SettingModel
from sqlalchemy.orm import Session
import json

class SettingClass:
    def __init__(self, db):
        self.db = db

    def get(self, id):
        try:
            data_query = self.db.query(SettingModel.id, SettingModel.dropbox_token, SettingModel.facebook_token, SettingModel.simplefactura_token, SettingModel.caf_limit, SettingModel.percentage_honorary_bill, SettingModel.apigetaway_token). \
                        filter(SettingModel.id == id). \
                        first()

            if data_query:
                setting_data = {
                    "id": data_query.id,
                    "dropbox_token": data_query.dropbox_token,
                    "facebook_token": data_query.facebook_token,
                    "simplefactura_token": data_query.simplefactura_token,
                    "caf_limit": data_query.caf_limit,
                    "percentage_honorary_bill": data_query.percentage_honorary_bill,
                    "apigetaway_token": data_query.apigetaway_token
                }

                result = {
                    "setting_data": setting_data
                }

                serialized_result = json.dumps(result)

                return serialized_result

            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def update(self, form_data):
        settings = self.db.query(SettingModel).filter(SettingModel.id == 1).first()

        settings.dropbox_token = form_data.dropbox_token
        settings.facebook_token = form_data.facebook_token
        settings.simplefactura_token = form_data.simplefactura_token
        settings.caf_limit = form_data.caf_limit
        settings.percentage_honorary_bill = form_data.percentage_honorary_bill
        settings.apigetaway_token = form_data.apigetaway_token

        self.db.commit()

        return settings