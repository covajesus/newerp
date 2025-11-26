from app.backend.db.models import CarbonMonoxideModel, BranchOfficeModel
from sqlalchemy import desc
from sqlalchemy.dialects import mysql
from datetime import datetime
import json

class CarbonMonoxideClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, branch_office_id=None, since_date=None, until_date=None, page=0, items_per_page=10):
        try:
            filters = []

            if branch_office_id is not None:
                filters.append(CarbonMonoxideModel.branch_office_id == branch_office_id)
            if since_date is not None and since_date != "":
                filters.append(CarbonMonoxideModel.added_date >= since_date)
            if until_date is not None and until_date != "":
                filters.append(CarbonMonoxideModel.added_date <= until_date)

            query = self.db.query(
                CarbonMonoxideModel.id, 
                CarbonMonoxideModel.branch_office_id,
                CarbonMonoxideModel.measure_value, 
                CarbonMonoxideModel.added_date,
                BranchOfficeModel.branch_office
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == CarbonMonoxideModel.branch_office_id
            ).filter(
                *filters
            ).order_by(
                desc(CarbonMonoxideModel.added_date)
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
                    "id": carbon_measure.id,
                    "branch_office_id": carbon_measure.branch_office_id,
                    "measure_value": carbon_measure.measure_value,
                    "added_date": carbon_measure.added_date.strftime('%d-%m-%Y') if carbon_measure.added_date else None,
                    "branch_office": carbon_measure.branch_office
                } for carbon_measure in data]

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
                    "id": carbon_measure.id,
                    "branch_office_id": carbon_measure.branch_office_id,
                    "measure_value": carbon_measure.measure_value,
                    "added_date": carbon_measure.added_date.strftime('%d-%m-%Y') if carbon_measure.added_date else None,
                    "branch_office": carbon_measure.branch_office
                } for carbon_measure in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
        
    def store(self, form_data, support):
        carbon_monoxide = CarbonMonoxideModel()
        
        carbon_monoxide.branch_office_id = form_data.branch_office_id
        carbon_monoxide.measure_value = form_data.measure_value
        carbon_monoxide.support = support
        carbon_monoxide.added_date = datetime.now()

        self.db.add(carbon_monoxide)

        try:
            self.db.commit()
            return {"status": "success", "message": "Carbon monoxide saved successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def get(self, id):
        try:
            data_query = self.db.query(CarbonMonoxideModel.id, CarbonMonoxideModel.measure_value, CarbonMonoxideModel.support, CarbonMonoxideModel.added_date, CarbonMonoxideModel.branch_office_id, BranchOfficeModel.branch_office). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == CarbonMonoxideModel.branch_office_id). \
                        order_by(CarbonMonoxideModel.id). \
                        filter(CarbonMonoxideModel.id == id). \
                        first()

            if data_query:
                carbon_monoxide_data = {
                    "id": data_query.id,
                    "branch_office_id": data_query.branch_office_id,
                    "support": data_query.support if data_query.support else "No hay archivo adjunto.",
                    "measure_value": data_query.measure_value,
                    "added_date": data_query.added_date.strftime('%d-%m-%Y') if data_query.added_date else None,
                    "branch_office": data_query.branch_office
                }

                result = {
                    "carbon_monoxide_data": carbon_monoxide_data
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
            self.db.query(CarbonMonoxideModel).filter(CarbonMonoxideModel.id == id).delete()
            self.db.commit()

            return {"status": "success", "message": "Carbon monoxide value deleted successfully"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}