from app.backend.db.models import SettingModel
from sqlalchemy.orm import Session
import json

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
                SettingModel.apigetaway_token
            ).filter(SettingModel.id == 1).first()

            if data_query:
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
                    "apigetaway_token": data_query.apigetaway_token
                }

                return {"setting_data": setting_data}

            else:
                return {"error": "No se encontraron datos para el campo especificado."}
            
        except Exception as e:
            return {"error": str(e)}

    
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

        self.db.commit()

        return settings
    
    def update_token(self, access_token):
        settings = self.db.query(SettingModel).filter(SettingModel.id == 1).first()

        settings.simplefactura_token = access_token

        self.db.commit()

        return settings