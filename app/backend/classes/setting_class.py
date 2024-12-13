from app.backend.db.models import SettingModel

class SettingClass:
    def __init__(self, db):
        self.db = db

    def get(self):
        settings = self.db.query(SettingModel).filter(SettingModel.id == 1).first()

        return settings