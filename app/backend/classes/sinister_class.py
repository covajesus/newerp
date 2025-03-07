from app.backend.db.models import SinisterModel, BranchOfficeModel
from sqlalchemy import desc
from sqlalchemy.dialects import mysql
from datetime import datetime
import json

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
                SinisterModel.sinister_date, 
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

            # Si se solicita paginación
            if page > 0:
                # Calcular el total de registros
                total_items = query.count()
                print(query.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))

                total_pages = (total_items + items_per_page - 1) // items_per_page
                print(total_pages)
                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                # Aplicar paginación en la consulta
                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                # Serializar los datos
                serialized_data = [{
                    "id": sinister.id,
                    "branch_office_id": sinister.branch_office_id,
                    "sinister_date": sinister.sinister_date.strftime('%d-%m-%Y') if sinister.sinister_date else None,
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
                    "sinister_date": sinister.sinister_date.strftime('%d-%m-%Y') if sinister.sinister_date else None,
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
        
    def store(self, form_data, support):
        # Crear una nueva instancia de ContractModel
        sinister = SinisterModel()
        sinister.branch_office_id = form_data.branch_office_id
        sinister.sinister_date = form_data.sinister_date
        sinister.client_name = form_data.client_name
        sinister.client_last_name = form_data.client_last_name
        sinister.client_phone = form_data.client_phone
        sinister.client_email = form_data.client_email
        sinister.brand = form_data.brand
        sinister.model = form_data.model
        sinister.year = form_data.year
        sinister.patent = form_data.patent
        sinister.color = form_data.color
        sinister.support = support
        sinister.added_date = datetime.now()

        # Añadir la nueva instancia a la base de datos
        self.db.add(sinister)

        # Intentar hacer commit y manejar posibles errores
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
                            SinisterModel.sinister_date,
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
                    "sinister_date": data_query.sinister_date.strftime('%d-%m-%Y') if data_query.sinister_date else None,
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

    def delete(self, id):
        try:
            self.db.query(SinisterModel).filter(SinisterModel.id == id).delete()
            self.db.commit()

            return {"status": "success", "message": "Sinister value deleted successfully"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}