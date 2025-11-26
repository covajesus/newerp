import requests
from sqlalchemy.orm import Session
from app.backend.db.models import DteSettingModel

class DteSettingClass:
    def __init__(self, db):
        self.db = db

    def get(self):
        data = self.db.query(DteSettingModel).first()

        return data
    
    def update(self, folio_quantity_sent):
        dte_settings =  self.db.query(DteSettingModel).filter(DteSettingModel.id == 1).first()
        dte_settings.folio_quantity_sent = folio_quantity_sent

        self.db.add(dte_settings)

        try:
            self.db.commit()

            return 1
        except Exception as e:
            return 0
    
    def last_folio_sent(self, last_folio_sent_date):
        dte_settings =  self.db.query(DteSettingModel).filter(DteSettingModel.id == 1).first()
        dte_settings.last_folio_sent_date = last_folio_sent_date

        self.db.add(dte_settings)

        try:
            self.db.commit()

            return 1
        except Exception as e:
            return 0
    
    def status(self, status):
        dte_settings =  self.db.query(DteSettingModel).filter(DteSettingModel.id == 1).first()
        dte_settings.status = status

        self.db.add(dte_settings)

        try:
            self.db.commit()

            return 1
        except Exception as e:
            return 0
        
    def verify(self):
        dte_settings =  self.db.query(DteSettingModel).filter(DteSettingModel.id == 1).first()
        dte_settings.last_folio_sent_date = 1

        self.db.add(dte_settings)

        try:
            self.db.commit()

            return 1
        except Exception as e:
            return 0