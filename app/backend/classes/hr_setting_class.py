from sqlalchemy.orm import Session
from app.backend.db.models import HrSettingModel

class HrSettingClass:
    def __init__(self, db: Session):
        self.db = db
              
    def get(self):
            data_query = self.db.query(HrSettingModel.id, HrSettingModel.percentage_honorary_bill, HrSettingModel.apigetaway_token). \
                        filter(HrSettingModel.id == 1). \
                        first()

            return data_query