from datetime import datetime
from sqlalchemy.orm import Session
from app.backend.db.models import BranchOfficeModel, PatentModel
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import aliased
import json

class PatentClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, period=None, page=0, items_per_page=10):
        try:
            # Inicialización de la variable data_query
            data_query = None

            # Comprobamos si la página es distinta de 0 y filtramos por sucursal si se proporciona el ID
            if page != 0:
                if period is not None:
                    # Incluir la información de la sucursal (BranchOfficeModel)
                    data_query = self.db.query(PatentModel.id, PatentModel.period, BranchOfficeModel.id.label("branch_office_id"), BranchOfficeModel.branch_office). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == PatentModel.branch_office_id). \
                        filter(PatentModel.period == period). \
                        order_by(PatentModel.id)
                else:
                    data_query = self.db.query(PatentModel.id, PatentModel.period, BranchOfficeModel.id.label("branch_office_id"), BranchOfficeModel.branch_office). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == PatentModel.branch_office_id). \
                        order_by(PatentModel.id)

                # Si data_query ha sido definida, realizamos la paginación
                if data_query:
                    total_items = data_query.count()
                    total_pages = (total_items + items_per_page - 1) // items_per_page

                    if page < 1 or page > total_pages:
                        return {"status": "error", "message": "Invalid page number"}

                    data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                    if not data:
                        return {"status": "error", "message": "No data found"}

                    serialized_data = [{
                        "id": patent.id,
                        "period": patent.period,
                        "branch_office": patent.branch_office,
                        "branch_office_id": patent.branch_office_id,
                    } for patent in data]  # Solo iteramos sobre los contratos

                    return {
                        "total_items": total_items,
                        "total_pages": total_pages,
                        "current_page": page,
                        "items_per_page": items_per_page,
                        "data": serialized_data
                    }

            # Si la página es 0, traer todos los registros sin paginación
            else:
                if period is not None:
                    data_query = self.db.query(PatentModel.id, PatentModel.period, BranchOfficeModel.id.label("branch_office_id"), BranchOfficeModel.branch_office). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == PatentModel.branch_office_id). \
                        filter(PatentModel.period == period). \
                        order_by(PatentModel.id).all()
                else:
                    data_query = self.db.query(PatentModel.id, PatentModel.period, BranchOfficeModel.id.label("branch_office_id"), BranchOfficeModel.branch_office). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == PatentModel.branch_office_id). \
                        order_by(PatentModel.id).all()

                # Serializar los datos y formatear las fechas
                serialized_data = [{
                    "id": patent.id,
                    "branch_office_id": patent.rut,
                    "branch_office": patent.branch_office,
                    "period": patent.client,
                } for patent in data_query]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
              
    def get(self, id):
        try:
            data_query = self.db.query(PatentModel.id, PatentModel.support, PatentModel.period, BranchOfficeModel.id.label("branch_office_id"), BranchOfficeModel.branch_office). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == PatentModel.branch_office_id). \
                        order_by(PatentModel.id). \
                        filter(PatentModel.id == id). \
                        first()

            if data_query:
                # Serializar los datos del empleado
                patent_data = {
                    "id": data_query.id,
                    "branch_office": data_query.branch_office,
                    "branch_office_id": data_query.branch_office_id,
                    "period": data_query.period,
                    "support": data_query.support
                }

                # Crear el resultado final como un diccionario
                result = {
                    "patent_data": patent_data
                }

                # Convierte el resultado a una cadena JSON
                serialized_result = json.dumps(result)

                return serialized_result

            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def store(self, form_data, support):
        # Crear una nueva instancia de ContractModel
        patent = PatentModel()
        
        # Asignar los valores del formulario a la instancia del modelo
        patent.branch_office_id = form_data.branch_office_id
        patent.period = form_data.period
        patent.support = support
        patent.added_date = datetime.now()

        # Añadir la nueva instancia a la base de datos
        self.db.add(patent)

        # Intentar hacer commit y manejar posibles errores
        try:
            self.db.commit()
            return {"status": "success", "message": "Patent saved successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def delete(self, id):
        try:
            # Borrar el contrato de la base de datos
            self.db.query(PatentModel).filter(PatentModel.id == id).delete()
            self.db.commit()

            return {"status": "success", "message": "Patent deleted successfully"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def update(self, id, form_data, support_file = None):
        """
        Actualiza los datos de la patente en la base de datos.
        """
        patent = self.db.query(PatentModel).filter(PatentModel.id == id).first()
        if not patent:
            raise HTTPException(status_code=404, detail="Patente no encontrada")

        # Actualizar campos
        patent.branch_office_id = form_data.branch_office_id
        patent.period = form_data.period
        if support_file != None:
            patent.support = support_file

        self.db.commit()
        self.db.refresh(patent)

