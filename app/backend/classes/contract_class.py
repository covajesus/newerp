from datetime import datetime
from sqlalchemy.orm import Session
from app.backend.db.models import ContractModel, BranchOfficeModel, ContractTypesModel
from datetime import datetime
from fastapi import HTTPException
import json


class ContractClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, branch_office_id=None, page=0, items_per_page=10):
        try:
            # Inicialización de la variable data_query
            data_query = None

            # Comprobamos si la página es distinta de 0 y filtramos por sucursal si se proporciona el ID
            if page != 0:
                if branch_office_id is not None:
                    # Incluir la información de la sucursal (BranchOfficeModel)
                    data_query = self.db.query(ContractModel.id, ContractModel.rut, ContractModel.client, ContractTypesModel.contract_type, ContractModel.start_date, ContractModel.duration, ContractModel.renovation_date, BranchOfficeModel.branch_office). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == ContractModel.branch_office_id). \
                        outerjoin(ContractTypesModel, ContractTypesModel.id == ContractModel.contract_type_id). \
                        filter(ContractModel.branch_office_id == branch_office_id). \
                        order_by(ContractModel.rut)
                else:
                    data_query = self.db.query(ContractModel.id, ContractModel.rut, ContractModel.client, ContractTypesModel.contract_type, ContractModel.start_date, ContractModel.duration, ContractModel.renovation_date, BranchOfficeModel.branch_office). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == ContractModel.branch_office_id). \
                        outerjoin(ContractTypesModel, ContractTypesModel.id == ContractModel.contract_type_id). \
                        order_by(ContractModel.rut)

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
                        "id": contract.id,
                        "rut": contract.rut,
                        "client": contract.client,
                        "contract_type": contract.contract_type,
                        "branch_office": contract.branch_office,
                        "start_date": contract.start_date.strftime('%d-%m-%Y') if contract.start_date else None,
                        "duration": contract.duration,
                        "renovation_date": contract.renovation_date.strftime('%d-%m-%Y') if contract.renovation_date else None
                    } for contract in data]  # Solo iteramos sobre los contratos

                    return {
                        "total_items": total_items,
                        "total_pages": total_pages,
                        "current_page": page,
                        "items_per_page": items_per_page,
                        "data": serialized_data
                    }

            # Si la página es 0, traer todos los registros sin paginación
            else:
                if branch_office_id is not None:
                    data_query = self.db.query(ContractModel.id, ContractTypesModel.contract_type, ContractModel.rut, ContractModel.client, ContractModel.start_date, ContractModel.duration, ContractModel.renovation_date, BranchOfficeModel.branch_office). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == ContractModel.branch_office_id). \
                        outerjoin(ContractTypesModel, ContractTypesModel.id == ContractModel.contract_type_id). \
                        filter(ContractModel.branch_office_id == branch_office_id). \
                        order_by(ContractModel.rut).all()
                else:
                    data_query = self.db.query(ContractModel.id, ContractTypesModel.contract_type, ContractModel.rut, ContractModel.client, ContractModel.start_date, ContractModel.duration, ContractModel.renovation_date, BranchOfficeModel.branch_office). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == ContractModel.branch_office_id). \
                        outerjoin(ContractTypesModel, ContractTypesModel.id == ContractModel.contract_type_id). \
                        order_by(ContractModel.rut).all()

                # Serializar los datos y formatear las fechas
                serialized_data = [{
                    "id": contract.id,
                    "rut": contract.rut,
                    "client": contract.client,
                    "contract_type": contract.contract_type,
                    "branch_office": contract.branch_office,
                    "start_date": contract.start_date.strftime('%d-%m-%Y') if contract.start_date else None,
                    "duration": contract.duration,
                    "renovation_date": contract.renovation_date.strftime('%d-%m-%Y') if contract.renovation_date else None
                } for contract in data_query]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
              
    def get(self, id):
        try:
            data_query = self.db.query(ContractModel.id, ContractModel.client_email, ContractModel.branch_office_id, ContractModel.address, ContractModel.support, ContractModel.rut, ContractModel.client, ContractTypesModel.contract_type, ContractModel.start_date, ContractModel.duration, ContractModel.renovation_date, BranchOfficeModel.branch_office). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == ContractModel.branch_office_id). \
                        outerjoin(ContractTypesModel, ContractTypesModel.id == ContractModel.contract_type_id). \
                        order_by(ContractModel.rut). \
                        filter(ContractModel.id == id). \
                        first()

            if data_query:
                # Serializar los datos del empleado
                contract_data = {
                    "id": data_query.id,
                    "branch_office_id": data_query.branch_office_id,
                    "address": data_query.address,
                    "rut": data_query.rut,
                    "client": data_query.client,
                    "client_email": data_query.client_email,
                    "contract_type": data_query.contract_type,
                    "start_date": data_query.start_date.isoformat(),
                    "duration": data_query.duration,
                    "renovation_date": data_query.renovation_date.isoformat(),
                    "branch_office": data_query.branch_office,
                    "support": data_query.support
                }

                # Crear el resultado final como un diccionario
                result = {
                    "contract_data": contract_data
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
        contract = ContractModel()
        
        # Asignar los valores del formulario a la instancia del modelo
        contract.branch_office_id = form_data.branch_office_id
        contract.contract_type_id = form_data.contract_type_id
        contract.rut = form_data.rut
        contract.client = form_data.client
        contract.client_email = form_data.client_email
        contract.start_date = form_data.start_date
        contract.renovation_date = form_data.renovation_date
        contract.duration = form_data.duration
        contract.address = form_data.address
        contract.support = support
        contract.added_date = datetime.now()

        # Añadir la nueva instancia a la base de datos
        self.db.add(contract)

        # Intentar hacer commit y manejar posibles errores
        try:
            self.db.commit()
            return {"status": "success", "message": "Contract saved successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def delete(self, id):
        try:
            # Borrar el contrato de la base de datos
            self.db.query(ContractModel).filter(ContractModel.id == id).delete()
            self.db.commit()

            return {"status": "success", "message": "Contract deleted successfully"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    
    def update(self, id, form_data, support_file = None):
        """
        Actualiza los datos del contrato en la base de datos.
        """
        contract = self.db.query(ContractModel).filter(ContractModel.id == id).first()
        if not contract:
            raise HTTPException(status_code=404, detail="Contrato no encontrado")

        # Actualizar campos
        contract.rut = form_data.rut
        contract.client = form_data.client
        contract.client_email = form_data.client_email
        contract.start_date = form_data.start_date
        contract.renovation_date = form_data.renovation_date
        contract.branch_office_id = form_data.branch_office_id
        contract.address = form_data.address
        contract.duration = form_data.duration
        contract.contract_type_id = form_data.contract_type_id
        if support_file != None:
            contract.support = support_file

        self.db.commit()
        self.db.refresh(contract)

