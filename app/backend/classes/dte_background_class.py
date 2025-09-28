import requests
from sqlalchemy.orm import Session
from app.backend.db.models import DteBackgroundModel

class DteBackgroundClass:
    def __init__(self, db):
        self.db = db
    
    def update(self, folio, inputs):
        dte_backgrounds =  self.db.query(DteBackgroundModel).filter(DteBackgroundModel.folio == folio).first()
        dte_backgrounds.status_sii_id = 1
        dte_backgrounds.track_id = inputs['track_id']
        dte_backgrounds.sii_date = inputs['sii_date']

        self.db.add(dte_backgrounds)

        try:
            self.db.commit()

            return 1
        except Exception as e:
            return 0