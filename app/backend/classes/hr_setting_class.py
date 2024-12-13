from app.backend.db.models import HrSettingModel

class HrSettingClass:
    def __init__(self, db):
        self.db = db

    def get(self):
        hr_settings = self.db.query(HrSettingModel).filter(HrSettingModel.id == 1).first()

        return hr_settings