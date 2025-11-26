from datetime import datetime
import json
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.backend.db.models import EmployeeIntershipModel, EmployeeIntershipAnswerModel, BranchOfficeModel, UserModel
from sqlalchemy import func

class EmployeeIntershipClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, branch_office_id=None, intern=None, rol_id=None, rut=None, page=0, items_per_page=10):
        try:
            filters = []

            if branch_office_id is not None:
                filters.append(EmployeeIntershipModel.branch_office_id == branch_office_id)
            if intern is not None:
                filters.append(EmployeeIntershipModel.intern == intern)

            if rol_id == 1 or rol_id == 2:
                query = self.db.query(
                    EmployeeIntershipModel.id, 
                    EmployeeIntershipModel.intern, 
                    EmployeeIntershipModel.branch_office_id, 
                    EmployeeIntershipModel.observations,
                    EmployeeIntershipModel.support,
                    func.date_format(EmployeeIntershipModel.added_date, "%d-%m-%Y").label("added_date"),
                    UserModel.full_name,
                    BranchOfficeModel.id.label("branch_office_id"), 
                    BranchOfficeModel.branch_office
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == EmployeeIntershipModel.branch_office_id
                ).outerjoin(
                    UserModel, UserModel.rut == EmployeeIntershipModel.intern
                ).filter(
                    *filters
                ).order_by(
                    EmployeeIntershipModel.added_date.desc()
                )
            else:
                query = self.db.query(
                    EmployeeIntershipModel.id, 
                    EmployeeIntershipModel.intern, 
                    EmployeeIntershipModel.branch_office_id, 
                    EmployeeIntershipModel.observations,
                    EmployeeIntershipModel.support,
                    func.date_format(EmployeeIntershipModel.added_date, "%d-%m-%Y").label("added_date"),
                    UserModel.full_name,
                    BranchOfficeModel.id.label("branch_office_id"), 
                    BranchOfficeModel.branch_office
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == EmployeeIntershipModel.branch_office_id
                ).outerjoin(
                    UserModel, UserModel.rut == EmployeeIntershipModel.intern
                ).filter(
                    EmployeeIntershipModel.intern == rut
                ).filter(
                    *filters
                ).order_by(
                    EmployeeIntershipModel.added_date.desc()
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
                    "observations": intership.observations,
                    "support": intership.support,
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
                    "observations": intership.observations,
                    "support": intership.support,
                    "added_date": intership.added_date,
                    "branch_office": intership.branch_office
                } for intership in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}

    def delete_employee_intership_answers(self, intership_id):
        intership_answer = self.db.query(EmployeeIntershipAnswerModel).filter(
            EmployeeIntershipAnswerModel.intership_id == intership_id
        ).all()

        for answer in intership_answer:
            intership_answer_detail = self.db.query(EmployeeIntershipAnswerModel).filter(
                EmployeeIntershipAnswerModel.id == answer.id,
            ).first()

            self.db.delete(intership_answer_detail)
            self.db.commit()
            
        
    def get_answers(self, intership_id, question):
        intership_answer = self.db.query(EmployeeIntershipAnswerModel).filter(
            EmployeeIntershipAnswerModel.intership_id == intership_id,
            EmployeeIntershipAnswerModel.question_id == question
        ).first()

        if not intership_answer:
            return {
                "answer": ''
            }
        else:
            return {
                "answer": intership_answer.answer_id
            }
        
    def get(self, id):
        try:
            data_query = self.db.query(
                            EmployeeIntershipModel.id, 
                            EmployeeIntershipModel.intern, 
                            EmployeeIntershipModel.branch_office_id,
                            EmployeeIntershipModel.observations,
                            EmployeeIntershipModel.support, 
                            func.date_format(EmployeeIntershipModel.added_date, "%d-%m-%Y").label("added_date"),
                            UserModel.full_name,
                            BranchOfficeModel.id.label("branch_office_id"), 
                            BranchOfficeModel.branch_office
                        ). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == EmployeeIntershipModel.branch_office_id). \
                        filter(EmployeeIntershipModel.id == id). \
                        first()

            if data_query:
                intership_data = {
                    "id": data_query.id,
                    "branch_office": data_query.branch_office,
                    "branch_office_id": data_query.branch_office_id,
                    "intern": data_query.intern,
                    "observations": data_query.observations,
                    "support": data_query.support,
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

    def store(self, branch_office_id, intern, observations, support):
        intership = EmployeeIntershipModel()
        
        intership.branch_office_id = branch_office_id
        intership.intern = intern
        intership.observations = observations
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