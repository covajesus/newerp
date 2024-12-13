from app.backend.db.models import AboutUsModel
from datetime import datetime
from sqlalchemy import func



class AboutUsClass:
    def __init__(self, db):
        self.db = db

    def update_about_us(self, data):
        about_us = self.db.query(AboutUsModel).first()
        about_us.text = data.text
        about_us.updated_date = datetime.now()

        self.db.commit()

        return 1
    
    def get_about_us(self):
        about_us = self.db.query(AboutUsModel).first()
        return about_us