from datetime import datetime
import json
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.backend.db.models import IntershipModel, IntershipAnswerModel, BranchOfficeModel, UserModel
from sqlalchemy import func

class IntershipClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, branch_office_id=None, intern=None, rol_id=None, rut=None, page=0, items_per_page=10):
        try:
            filters = []

            if branch_office_id is not None:
                filters.append(IntershipModel.branch_office_id == branch_office_id)
            if intern is not None:
                filters.append(IntershipModel.intern == intern)

            if rol_id == 1 or rol_id == 2:
                query = self.db.query(
                    IntershipModel.id, 
                    IntershipModel.intern, 
                    IntershipModel.branch_office_id, 
                    func.date_format(IntershipModel.added_date, "%d-%m-%Y").label("added_date"),
                    UserModel.full_name,
                    BranchOfficeModel.id.label("branch_office_id"), 
                    BranchOfficeModel.branch_office
                ).join(
                    UserModel, UserModel.rut == IntershipModel.intern
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == IntershipModel.branch_office_id
                ).filter(
                    *filters
                ).order_by(
                    IntershipModel.added_date.desc()
                )
            else:
                query = self.db.query(
                    IntershipModel.id, 
                    IntershipModel.intern, 
                    IntershipModel.branch_office_id, 
                    func.date_format(IntershipModel.added_date, "%d-%m-%Y").label("added_date"),
                    UserModel.full_name,
                    BranchOfficeModel.id.label("branch_office_id"), 
                    BranchOfficeModel.branch_office
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == IntershipModel.branch_office_id
                ).outerjoin(
                    UserModel, UserModel.rut == IntershipModel.intern
                ).filter(
                    IntershipModel.intern == rut
                ).filter(
                    *filters
                ).order_by(
                    IntershipModel.added_date.desc()
                )

            if page > 0:
                total_items = query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                serialized_data = [{
                    "id": intership.id,
                    "branch_office_id": intership.branch_office_id,
                    "intern": intership.intern,
                    "full_name": intership.full_name,
                    "added_date": intership.added_date,
                    "branch_office": intership.branch_office
                } for intership in data]

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }

            else:
                data = query.all()

                serialized_data = [{
                    "id": intership.id,
                    "branch_office_id": intership.branch_office_id,
                    "intern": intership.intern,
                    "full_name": intership.full_name,
                    "added_date": intership.added_date,
                    "branch_office": intership.branch_office
                } for intership in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
        
    def get_answers(self, intership_id, question):
        intership_answer = self.db.query(IntershipAnswerModel).filter(
            IntershipAnswerModel.intership_id == intership_id,
            IntershipAnswerModel.question_id == question
        ).first()

        if not intership_answer:
            return {
                "answer": '',
                "observation": '',
                "image": ''
            }
        else:
            return {
                "answer": intership_answer.answer_id,
                "observation": intership_answer.observation,
                "image": intership_answer.support
            }
        
    def get(self, id):
        try:
            data_query = self.db.query(
                            IntershipModel.id, 
                            IntershipModel.intern, 
                            IntershipModel.branch_office_id, 
                            func.date_format(IntershipModel.added_date, "%d-%m-%Y").label("added_date"),
                            UserModel.full_name,
                            BranchOfficeModel.id.label("branch_office_id"), 
                            BranchOfficeModel.branch_office
                        ). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == IntershipModel.branch_office_id). \
                        filter(IntershipModel.id == id). \
                        first()

            if data_query:
                intership_data = {
                    "id": data_query.id,
                    "branch_office": data_query.branch_office,
                    "branch_office_id": data_query.branch_office_id,
                    "intern": data_query.intern,
                    "full_name": data_query.full_name,
                    "added_date": data_query.added_date
                }

                result = {
                    "intership_data": intership_data
                }

                serialized_result = json.dumps(result)

                return serialized_result
            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def store(self, branch_office_id, intern):
        intership = IntershipModel()
        
        intership.branch_office_id = branch_office_id
        intership.intern = intern
        intership.added_date = datetime.now()

        self.db.add(intership)

        try:
            self.db.commit()
            return intership.id
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def store_answer(self, intership_id, question_id, answer_id, observation, support):
        intership_answer = IntershipAnswerModel()

        intership_answer.intership_id = intership_id
        intership_answer.question_id = question_id
        intership_answer.answer_id = answer_id
        intership_answer.observation = observation
        intership_answer.support = support
        intership_answer.added_date = datetime.now()

        self.db.add(intership_answer)
        self.db.commit()

    def delete(self, id):
        try:
            self.db.query(IntershipModel).filter(IntershipModel.id == id).delete()
            self.db.commit()

            return {"status": "success", "message": "Intership deleted successfully"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}