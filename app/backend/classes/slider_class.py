from app.backend.db.models import SliderModel
from datetime import datetime
from sqlalchemy import func
from app.backend.classes.helper_class import HelperClass
from app.backend.classes.dropbox_class import DropboxClass
import os
import json

class SliderClass:
    def __init__(self, db):
        self.db = db

       
    def upload_image(self, file):
        slider = SliderModel()
        slider.support = file
        slider.added_date = datetime.now()
        slider.updated_date = datetime.now()

        self.db.add(slider)
        self.db.commit()
        
        return 1
    
    def delete(self, id):
        data = self.db.query(SliderModel).filter(SliderModel.id == id ).first()
        support = data.support
        self.db.delete(data)
        self.db.commit()
        
        return support
    
    def get(self):
        data = self.db.query(SliderModel).all()
        return data