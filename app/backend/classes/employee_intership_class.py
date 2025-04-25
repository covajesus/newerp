from datetime import datetime
import json
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.backend.db.models import EmployeeIntershipModel, EmployeeIntershipAnswerModel, BranchOfficeModel, UserModel
from sqlalchemy import func

class EmployeeIntershipClass:
    def __init__(self, db: Session):
        self.db = db


    def store(self, branch_office_id, intern, observation, support):
        intership = EmployeeIntershipModel()
        
        intership.branch_office_id = branch_office_id
        intership.intern = intern
        intership.observation = observation
        intership.support = support
        intership.added_date = datetime.now()

        self.db.add(intership)

        try:
            self.db.commit()
            return intership.id
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def store_answer(self, intership_id, question_id, answer_id):
        intership_answer = EmployeeIntershipAnswerModel()

        intership_answer.intership_id = intership_id
        intership_answer.question_id = question_id
        intership_answer.answer_id = answer_id
        intership_answer.added_date = datetime.now()

        self.db.add(intership_answer)
        self.db.commit()