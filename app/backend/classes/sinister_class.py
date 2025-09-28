from app.backend.db.models import SinisterModel, BranchOfficeModel, SinisterReviewModel
from sqlalchemy import desc
from sqlalchemy.dialects import mysql
from datetime import date, datetime
import json
from fastapi import HTTPException

class SinisterClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, branch_office_id=None, page=0, items_per_page=10):
        try:
            filters = []

            if branch_office_id is not None:
                filters.append(SinisterModel.branch_office_id == branch_office_id)

            query = self.db.query(
                SinisterModel.id, 
                SinisterModel.branch_office_id,
                SinisterModel.sinister_type_id,
                SinisterModel.protected_area_id,
                SinisterModel.registered_event_id,
                SinisterModel.notified_security_id,
                SinisterModel.denounced_authorities_id,
                SinisterModel.status_id,
                SinisterModel.sinister_date, 
                SinisterModel.client_rut,
                SinisterModel.client_name,
                SinisterModel.client_last_name,
                SinisterModel.client_phone,
                SinisterModel.client_email,
                SinisterModel.brand,
                SinisterModel.model,
                SinisterModel.year,
                SinisterModel.patent,
                SinisterModel.color,
                BranchOfficeModel.branch_office,
                SinisterModel.support
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == SinisterModel.branch_office_id
            ).filter(
                *filters
            ).order_by(
                desc(SinisterModel.added_date)
            )

            if page > 0:
                total_items = query.count()
                print(query.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))

                total_pages = (total_items + items_per_page - 1) // items_per_page
                print(total_pages)
                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                serialized_data = [{
                    "id": sinister.id,
                    "branch_office_id": sinister.branch_office_id,
                    "status_id": sinister.status_id,
                    "sinister_type_id": sinister.sinister_type_id,
                    "protected_area_id": sinister.protected_area_id,
                    "registered_event_id": sinister.registered_event_id,
                    "notified_security_id": sinister.notified_security_id,
                    "denounced_authorities_id": sinister.denounced_authorities_id,
                    "sinister_date": sinister.sinister_date,
                    "client_rut": sinister.client_rut,
                    "client_name": sinister.client_name,
                    "client_last_name": sinister.client_last_name,
                    "client_phone": sinister.client_phone,
                    "client_email": sinister.client_email,
                    "brand": sinister.brand,
                    "model": sinister.model,
                    "year": sinister.year,
                    "patent": sinister.patent,
                    "color": sinister.color,
                    "branch_office": sinister.branch_office,
                    "support": sinister.support
                } for sinister in data]

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
                    "id": sinister.id,
                    "branch_office_id": sinister.branch_office_id,
                    "status_id": sinister.status_id,
                    "sinister_type_id": sinister.sinister_type_id,
                    "protected_area_id": sinister.protected_area_id,
                    "registered_event_id": sinister.registered_event_id,
                    "notified_security_id": sinister.notified_security_id,
                    "denounced_authorities_id": sinister.denounced_authorities_id,
                    "sinister_date": sinister.sinister_date,
                    "client_rut": sinister.client_rut,
                    "client_name": sinister.client_name,
                    "client_last_name": sinister.client_last_name,
                    "client_phone": sinister.client_phone,
                    "client_email": sinister.client_email,
                    "brand": sinister.brand,
                    "model": sinister.model,
                    "year": sinister.year,
                    "patent": sinister.patent,
                    "color": sinister.color,
                    "branch_office": sinister.branch_office,
                    "support": sinister.support
                } for sinister in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}

    def store_review(self, form_data, support):
        sinister_review = SinisterReviewModel()
        sinister_review.sinister_id = form_data.sinister_id
        sinister_review.sinister_step_type_id = form_data.sinister_step_type_id
        sinister_review.review_description = form_data.review_description
        sinister_review.support = support
        sinister_review.added_date = datetime.now()

        self.db.add(sinister_review)
        
        self.db.commit()

        if form_data.sinister_step_type_id == 2:
            status_id = 10
        elif form_data.sinister_step_type_id == 3:
            status_id = 11
        elif form_data.sinister_step_type_id == 4:
            status_id = 12
        elif form_data.sinister_step_type_id == 5:
            status_id = 13

        self.update(form_data.sinister_id, None, status_id)

          
    def store(self, form_data, support):
        sinister = SinisterModel()
        sinister.branch_office_id = form_data.branch_office_id
        sinister.sinister_type_id = form_data.sinister_type_id
        sinister.protected_area_id = form_data.protected_area_id
        sinister.registered_event_id = form_data.registered_event_id
        sinister.notified_security_id = form_data.notified_security_id
        sinister.denounced_authorities_id = form_data.denounced_authorities_id
        sinister.status_id = 1
        sinister.sinister_date = form_data.sinister_date
        sinister.client_name = form_data.client_name
        sinister.client_rut = form_data.client_rut
        sinister.client_last_name = form_data.client_last_name
        sinister.client_phone = form_data.client_phone
        sinister.client_email = form_data.client_email
        sinister.brand = form_data.brand
        sinister.model = form_data.model
        sinister.year = form_data.year
        sinister.patent = form_data.patent
        sinister.color = form_data.color
        sinister.description = form_data.description
        sinister.support = support
        sinister.added_date = datetime.now()

        self.db.add(sinister)

        try:
            self.db.commit()
            return {"status": "success", "message": "Sinister saved successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def get(self, id):
        try:
            data_query = self.db.query(
                            SinisterModel.id,
                            SinisterModel.branch_office_id,
                            SinisterModel.status_id,
                            SinisterModel.sinister_type_id,
                            SinisterModel.protected_area_id,
                            SinisterModel.registered_event_id,
                            SinisterModel.notified_security_id,
                            SinisterModel.denounced_authorities_id,
                            SinisterModel.sinister_date,
                            SinisterModel.description,
                            SinisterModel.client_rut,
                            SinisterModel.client_name,
                            SinisterModel.client_last_name,
                            SinisterModel.client_phone,
                            SinisterModel.client_email,
                            SinisterModel.brand,
                            SinisterModel.model,
                            SinisterModel.year,
                            SinisterModel.patent,
                            SinisterModel.color,
                            BranchOfficeModel.branch_office,
                            SinisterModel.support
                        ). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == SinisterModel.branch_office_id). \
                        order_by(SinisterModel.id). \
                        filter(SinisterModel.id == id). \
                        first()

            if data_query:
                sinister_data = {
                    "id": data_query.id,
                    "branch_office_id": data_query.branch_office_id,
                    "status_id": data_query.status_id,
                    "sinister_type_id": data_query.sinister_type_id,
                    "protected_area_id": data_query.protected_area_id,
                    "registered_event_id": data_query.registered_event_id,
                    "notified_security_id": data_query.notified_security_id,
                    "denounced_authorities_id": data_query.denounced_authorities_id,
                    "description": data_query.description,
                    "sinister_date": data_query.sinister_date.strftime('%Y-%m-%d %H:%M:%S') if isinstance(data_query.sinister_date, (date, datetime)) else data_query.sinister_date,
                    "client_rut": data_query.client_rut,
                    "client_name": data_query.client_name,
                    "client_last_name": data_query.client_last_name,
                    "client_phone": data_query.client_phone,
                    "client_email": data_query.client_email,
                    "brand": data_query.brand,
                    "model": data_query.model,
                    "year": data_query.year,
                    "patent": data_query.patent,
                    "color": data_query.color,
                    "branch_office": data_query.branch_office,
                    "support": data_query.support
                }

                result = {
                    "sinister_data": sinister_data
                }

                serialized_result = json.dumps(result)

                return serialized_result

            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def get_sinister_review(self, id, sinister_step_type_id):
        try:
            data_query = self.db.query(
                            SinisterReviewModel.id,
                            SinisterReviewModel.sinister_id,
                            SinisterReviewModel.sinister_step_type_id,
                            SinisterReviewModel.review_description,
                            SinisterReviewModel.support
                        ). \
                        filter(SinisterReviewModel.sinister_id == id). \
                        filter(SinisterReviewModel.sinister_step_type_id == sinister_step_type_id). \
                        first()

            if data_query:
                sinister_data = {
                    "id": data_query.id,
                    "sinister_id": data_query.sinister_id,
                    "sinister_step_type_id": data_query.sinister_step_type_id,
                    "review_description": data_query.review_description,
                    "support": data_query.support
                }

                result = {
                    "sinister_data": sinister_data
                }

                serialized_result = json.dumps(result)

                return serialized_result

            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            self.db.query(SinisterModel).filter(SinisterModel.id == id).delete()
            self.db.commit()

            return {"status": "success", "message": "Sinister value deleted successfully"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def update(self, id, answer=None, status_id=None, sinister_version_id=None):
        sinister = self.db.query(SinisterModel).filter(SinisterModel.id == id).first()
        if not sinister:
            raise HTTPException(status_code=404, detail="Patente no encontrada")
        
        if answer != None:
            if sinister_version_id == 1:
                if answer == 1:
                    sinister.status_id = 9
                else:
                    sinister.status_id = 3
            else:
                sinister.status_id = 11
        else:
            sinister.status_id = status_id

        self.db.commit()
        self.db.refresh(sinister)