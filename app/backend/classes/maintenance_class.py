from datetime import datetime
import json
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.backend.db.models import MaintenanceModel, MaintenanceDataModel, BranchOfficeModel
from sqlalchemy import func

class MaintenanceClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, branch_office_id=None, page=0, items_per_page=10):
        try:
            filters = []
            if branch_office_id is not None:
                filters.append(MaintenanceModel.branch_office_id == branch_office_id)

            query = self.db.query(
                    MaintenanceModel.id, 
                    func.date_format(MaintenanceModel.maintenance_date, "%d-%m-%Y").label("maintenance_date"),
                    func.date_format(MaintenanceModel.added_date, "%d-%m-%Y").label("added_date"),
                    BranchOfficeModel.id.label("branch_office_id"), 
                    BranchOfficeModel.branch_office
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == MaintenanceModel.branch_office_id
                ).filter(
                    *filters
                ).order_by(
                    MaintenanceModel.maintenance_date.desc()
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
                    "id": maintenance.id,
                    "branch_office_id": maintenance.branch_office_id,
                    "maintenance_date": maintenance.maintenance_date,
                    "added_date": maintenance.added_date,
                    "branch_office": maintenance.branch_office
                } for maintenance in data]

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
                    "id": maintenance.id,
                    "branch_office_id": maintenance.branch_office_id,
                    "maintenance_date": maintenance.maintenance_date,
                    "added_date": maintenance.added_date,
                    "branch_office": maintenance.branch_office
                } for maintenance in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
        
    def get_files(self, id, maintenance_id):
        maintenance_datum = self.db.query(MaintenanceDataModel).filter(
            MaintenanceDataModel.file_number == id,
            MaintenanceDataModel.maintenance_id == maintenance_id
        ).first()

        if not maintenance_datum:
            return {
                "file": ''
            }
        else:
            return {
                "file": maintenance_datum.support
            }

    def get_all_details(self, maintenance_id):
        try:
            data_query = self.db.query(
                MaintenanceDataModel.id,
                MaintenanceDataModel.file_number,
                MaintenanceDataModel.support,
            ).filter(
                MaintenanceDataModel.maintenance_id == maintenance_id
            ).all()

            if data_query:
                # Devolver una lista de resultados
                maintenance_data_list = [
                    {
                        "id": row.id,
                        "file_number": row.file_number,
                        "support": row.support,
                    }
                    for row in data_query
                ]

                result = {
                    "maintenance_data": maintenance_data_list
                }

                return json.dumps(result)
            else:
                return json.dumps({"maintenance_data": []})

        except Exception as e:
            return json.dumps({"error": str(e)})

    def get(self, id):
        try:
            data_query = self.db.query(
                            MaintenanceModel.id, 
                            func.date_format(MaintenanceModel.maintenance_date, "%d-%m-%Y").label("maintenance_date"),
                            func.date_format(MaintenanceModel.added_date, "%d-%m-%Y").label("added_date"),
                            BranchOfficeModel.id.label("branch_office_id"), 
                            BranchOfficeModel.branch_office
                        ). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == MaintenanceModel.branch_office_id). \
                        filter(MaintenanceModel.id == id). \
                        first()

            if data_query:
                maintenance_data = {
                    "id": data_query.id,
                    "branch_office_id": data_query.branch_office_id,
                    "maintenance_date": data_query.maintenance_date,
                    "added_date": data_query.added_date,
                    "branch_office": data_query.branch_office
                }

                result = {
                    "maintenance_data": maintenance_data
                }

                serialized_result = json.dumps(result)

                return serialized_result
            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def store(self, branch_office_id, maintenance_date):
        maintenance = MaintenanceModel()
        
        maintenance.branch_office_id = branch_office_id
        maintenance.maintenance_date = maintenance_date
        maintenance.added_date = datetime.now()

        self.db.add(maintenance)

        try:
            self.db.commit()
            return maintenance.id
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def store_datum(self, maintenance_id, file_number, support):
        maintenance_datum = MaintenanceDataModel()

        maintenance_datum.maintenance_id = maintenance_id
        maintenance_datum.file_number = file_number
        maintenance_datum.support = support
        maintenance_datum.added_date = datetime.now()

        self.db.add(maintenance_datum)
        self.db.commit()

    def delete(self, id):
        try:
            self.db.query(MaintenanceModel).filter(MaintenanceModel.id == id).delete()
            self.db.commit()

            return {"status": "success", "message": "Maintenance deleted successfully"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def delete_datum(self, maintenance_id):
        try:
            self.db.query(MaintenanceDataModel).filter(MaintenanceDataModel.maintenance_id == maintenance_id).delete()
            self.db.commit()

            return {"status": "success", "message": "Maintenance data deleted successfully"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}