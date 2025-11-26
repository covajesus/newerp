from app.backend.db.models import LogoModel
from datetime import datetime
from sqlalchemy import func
from app.backend.classes.helper_class import HelperClass
from app.backend.classes.dropbox_class import DropboxClass
import os
import json

class LogoClass:
    def __init__(self, db):
        self.db = db

       
    def upload_logo(self, file):
        logo = LogoModel()
        logo.support = file
        logo.added_date = datetime.now()
        logo.updated_date = datetime.now()

        self.db.add(logo)
        self.db.commit()
        
        return 1
    
    def delete(self, id):
        data = self.db.query(LogoModel).filter(LogoModel.id == id ).first()
        support = data.support
        self.db.delete(data)
        self.db.commit()
        
        return support
    
    def get(self):
        data = self.db.query(LogoModel).order_by(LogoModel.id.desc()).first()
        return data