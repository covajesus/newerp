from datetime import datetime
from sqlalchemy.orm import Session
from app.backend.db.models import BranchOfficeModel, DemarcationModel
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import aliased
import json

class DemarcationClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, page=0, items_per_page=10):
        try:

            query = self.db.query(
                DemarcationModel.id, 
                DemarcationModel.branch_office_id,
                BranchOfficeModel.branch_office,
                DemarcationModel.labor_costs,
                DemarcationModel.material_costs,
                DemarcationModel.made_arrows,
                DemarcationModel.made_pedestrian_crossing,
                DemarcationModel.made_disability,
                DemarcationModel.made_island,
                DemarcationModel.made_pregnant,
                DemarcationModel.made_wall,
                DemarcationModel.added_date,
                DemarcationModel.updated_date
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == DemarcationModel.branch_office_id
            ).order_by(
                DemarcationModel.id
            )

            # Si se solicita paginación
            if page > 0:
                # Calcular el total de registros
                total_items = query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                # Aplicar paginación en la consulta
                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                # Serializar los datos
                serialized_data = [{
                    "id": demarcation.id,
                    "branch_office_id": demarcation.branch_office_id,
                    "branch_office": demarcation.branch_office,
                    "labor_costs": demarcation.labor_costs,
                    "material_costs": demarcation.material_costs,
                    "made_arrows": demarcation.made_arrows,
                    "made_pedestrian_crossing": demarcation.made_pedestrian_crossing,
                    "made_disability": demarcation.made_disability,
                    "made_island": demarcation.made_island,
                    "made_pregnant": demarcation.made_pregnant,
                    "made_wall": demarcation.made_wall,
                    "added_date": demarcation.added_date
                } for demarcation in data]

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }

            # Si no se solicita paginación, traer todos los datos
            else:
                data = query.all()

                # Serializar los datos
                serialized_data = [{
                    "id": demarcation.id,
                    "branch_office_id": demarcation.branch_office_id,
                    "branch_office": demarcation.branch_office,
                    "labor_costs": demarcation.labor_costs,
                    "material_costs": demarcation.material_costs,
                    "made_arrows": demarcation.made_arrows,
                    "made_pedestrian_crossing": demarcation.made_pedestrian_crossing,
                    "made_road_signage": demarcation.made_road_signage,
                    "made_disability": demarcation.made_disability,
                    "made_island": demarcation.made_island,
                    "made_pregnant": demarcation.made_pregnant,
                    "made_wall": demarcation.made_wall,
                    "added_date": demarcation.added_date
                } for demarcation in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
              
    def get(self, id):
        try:
            data_query = self.db.query(
                                DemarcationModel.id, 
                                DemarcationModel.branch_office_id,
                                BranchOfficeModel.branch_office,
                                DemarcationModel.labor_costs,
                                DemarcationModel.material_costs,
                                DemarcationModel.made_arrows,
                                DemarcationModel.made_pedestrian_crossing,
                                DemarcationModel.made_disability,
                                DemarcationModel.made_island,
                                DemarcationModel.made_pregnant,
                                DemarcationModel.made_wall,
                                DemarcationModel.file_made_arrows,
                                DemarcationModel.file_made_pedestrian_crossing,
                                DemarcationModel.file_made_disability,
                                DemarcationModel.file_made_island,
                                DemarcationModel.file_made_pregnant,
                                DemarcationModel.file_made_wall,
                                DemarcationModel.added_date,
                                DemarcationModel.updated_date
                            ). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == DemarcationModel.branch_office_id). \
                        filter(DemarcationModel.id == id). \
                        first()

            if data_query:
                # Serializar los datos del empleado
                demarcation_data = {
                    "id": data_query.id,
                    "branch_office_id": data_query.branch_office_id,
                    "branch_office": data_query.branch_office,
                    "labor_costs": data_query.labor_costs,
                    "material_costs": data_query.material_costs,
                    "made_arrows": data_query.made_arrows,
                    "made_pedestrian_crossing": data_query.made_pedestrian_crossing,
                    "made_disability": data_query.made_disability,
                    "made_island": data_query.made_island,
                    "made_pregnant": data_query.made_pregnant,
                    "made_wall": data_query.made_wall,
                    "file_made_arrows": data_query.file_made_arrows,
                    "file_made_pedestrian_crossing": data_query.file_made_pedestrian_crossing,
                    "file_made_disability": data_query.file_made_disability,
                    "file_made_island": data_query.file_made_island,
                    "file_made_pregnant": data_query.file_made_pregnant,
                    "file_made_wall": data_query.file_made_wall
                }

                # Crear el resultado final como un diccionario
                result = {
                    "demarcation_data": demarcation_data
                }

                # Convierte el resultado a una cadena JSON
                serialized_result = json.dumps(result)

                return serialized_result

            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def store(self, form_data, remote_path1, remote_path2, remote_path3, remote_path4, remote_path5, remote_path6):
        demarcation = DemarcationModel()
        demarcation.branch_office_id = form_data.branch_office_id
        demarcation.material_costs = form_data.material_costs
        demarcation.labor_costs = form_data.labor_costs
        demarcation.made_arrows = form_data.made_arrows
        demarcation.made_pedestrian_crossing = form_data.made_pedestrian_crossing
        demarcation.made_disability = form_data.made_disability
        demarcation.made_island = form_data.made_island
        demarcation.made_pregnant = form_data.made_pregnant
        demarcation.made_wall = form_data.made_wall
        demarcation.file_made_arrows = remote_path1
        demarcation.file_made_pedestrian_crossing = remote_path2
        demarcation.file_made_disability = remote_path3
        demarcation.file_made_island = remote_path4
        demarcation.file_made_pregnant = remote_path5
        demarcation.file_made_wall = remote_path6
        demarcation.added_date = datetime.now()

        self.db.add(demarcation)

        try:
            self.db.commit()
            return {"status": "success", "message": "Demarcation saved successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def delete(self, id):
        try:
            self.db.query(DemarcationModel).filter(DemarcationModel.id == id).delete()
            self.db.commit()

            return {"status": "success", "message": "Demarcation deleted successfully"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def update(self, id, form_data, support_file = None):
        demarcation = self.db.query(DemarcationModel).filter(DemarcationModel.id == id).first()
        if not demarcation:
            raise HTTPException(status_code=404, detail="Demarcación no encontrada")

        demarcation.branch_office_id = form_data.branch_office_id
        demarcation.material_parking_line_costs = form_data.material_parking_line_costs
        demarcation.labor_parking_line_costs = form_data.labor_parking_line_costs
        demarcation.material_road_signage_costs = form_data.material_road_signage_costs
        demarcation.labor_road_signage_costs = form_data.labor_road_signage_costs
        demarcation.material_disability_costs = form_data.material_disability_costs
        demarcation.labor_disability_costs = form_data.labor_disability_costs
        demarcation.material_island_costs = form_data.material_island_costs
        demarcation.labor_island_costs = form_data.labor_island_costs
        demarcation.material_pregnant_costs = form_data.material_pregnant_costs
        demarcation.labor_pregnant_costs = form_data.labor_pregnant_costs
        demarcation.material_wall_costs = form_data.material_wall_costs
        demarcation.labor_wall_costs = form_data.labor_wall_costs
        demarcation.updated_date = datetime.now()

        self.db.commit()
        self.db.refresh(demarcation)

