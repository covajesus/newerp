from datetime import datetime
from sqlalchemy.orm import Session
from app.backend.db.models import ContractModel, BranchOfficeModel, ContractTypesModel
from datetime import datetime
from fastapi import HTTPException
import json


class ContractClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, rut=None, branch_office_id=None, page=0, items_per_page=10):
        try:
            # Construcción de la consulta base
            query = self.db.query(
                ContractModel.id,
                ContractModel.rut,
                ContractModel.client,
                ContractTypesModel.contract_type,
                ContractModel.start_date,
                ContractModel.end_date,
                ContractModel.amount,
                ContractModel.renovation_date,
                BranchOfficeModel.branch_office
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == ContractModel.branch_office_id
            ).outerjoin(
                ContractTypesModel, ContractTypesModel.id == ContractModel.contract_type_id
            ).order_by(
                ContractModel.rut
            )

            # Aplicar filtros según los parámetros
            if rut:
                query = query.filter(ContractModel.rut == rut)
            if branch_office_id:
                query = query.filter(ContractModel.branch_office_id == branch_office_id)

            if page == 0:
                # Si la página es 0, devolver todos los resultados sin paginación
                data = query.all()
                return [{
                    "id": contract.id,
                    "rut": contract.rut,
                    "client": contract.client,
                    "contract_type": contract.contract_type,
                    "branch_office": contract.branch_office,
                    "start_date": contract.start_date.strftime('%d-%m-%Y') if contract.start_date else None,
                    "end_date": contract.end_date.strftime('%d-%m-%Y') if contract.end_date else None,
                    "amount": contract.amount,
                    "renovation_date": contract.renovation_date.strftime('%d-%m-%Y') if contract.renovation_date else None
                } for contract in data]

            # Paginación
            total_items = query.count()
            total_pages = (total_items + items_per_page - 1) // items_per_page

            if page < 1 or page > total_pages:
                return {"status": "error", "message": "Invalid page number"}

            data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

            if not data:
                return {"status": "error", "message": "No data found"}

            return {
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "items_per_page": items_per_page,
                "data": [{
                    "id": contract.id,
                    "rut": contract.rut,
                    "client": contract.client,
                    "contract_type": contract.contract_type,
                    "branch_office": contract.branch_office,
                    "start_date": contract.start_date.strftime('%d-%m-%Y') if contract.start_date else None,
                    "end_date": contract.end_date.strftime('%d-%m-%Y') if contract.end_date else None,
                    "amount": contract.amount,
                    "renovation_date": contract.renovation_date.strftime('%d-%m-%Y') if contract.renovation_date else None
                } for contract in data]
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}
              
    def get(self, id):
        try:
            data_query = self.db.query(ContractModel.id, ContractModel.amount, ContractModel.currency, ContractModel.branch_office_id, ContractModel.address, ContractModel.support, ContractModel.rut, ContractModel.client, ContractTypesModel.contract_type, ContractModel.start_date, ContractModel.end_date, ContractModel.renovation_date, BranchOfficeModel.branch_office). \
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
                    "contract_type": data_query.contract_type,
                    "start_date": data_query.start_date.isoformat(),
                    "end_date": data_query.end_date.isoformat(),
                    "renovation_date": data_query.renovation_date.isoformat(),
                    "currency": data_query.currency,
                    "amount": data_query.amount,
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
        contract.start_date = form_data.start_date
        contract.end_date = form_data.end_date
        contract.renovation_date = form_data.renovation_date
        contract.address = form_data.address
        contract.currency = form_data.currency
        contract.amount = form_data.amount
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
        contract.amount = form_data.amount
        contract.end_date = form_data.end_date
        contract.start_date = form_data.start_date
        contract.renovation_date = form_data.renovation_date
        contract.branch_office_id = form_data.branch_office_id
        contract.currency = form_data.currency
        contract.address = form_data.address
        contract.contract_type_id = form_data.contract_type_id
        if support_file != None:
            contract.support = support_file

        self.db.commit()
        self.db.refresh(contract)

