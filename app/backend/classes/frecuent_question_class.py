from app.backend.db.models import FrecuentQuestionModel
from datetime import datetime
from sqlalchemy import func



class FrecuentQuestionClass:
    def __init__(self, db):
        self.db = db

    def update(self, data):
        frecuent_question = self.db.query(FrecuentQuestionModel).first()
        frecuent_question.title = data.title
        frecuent_question.description = data.description
        frecuent_question.added_date = datetime.now()
        frecuent_question.updated_date = datetime.now()
        
        self.db.commit()

        return 1
    
    def get_all(self):
        frecuent_question = self.db.query(FrecuentQuestionModel).all()
        return frecuent_question
    
    def store(self, data):
        frecuent_question  = FrecuentQuestionModel()
        frecuent_question.question = data.question
        frecuent_question.answer = data.answer
        frecuent_question.added_date = datetime.now()
        frecuent_question.updated_date = datetime.now()

        self.db.add(frecuent_question)
        self.db.commit()
        return 1
    
    def delete(self, id):
        frecuent_question = self.db.query(FrecuentQuestionModel).filter(FrecuentQuestionModel.id == id).first()
        self.db.delete(frecuent_question)
        self.db.commit()
        return 1
    
    