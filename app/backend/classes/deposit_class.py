from datetime import datetime
from sqlalchemy.orm import Session
from app.backend.db.models import BranchOfficeModel, DepositModel
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import aliased
import json
from sqlalchemy import case
from app.backend.db.models import DepositModel, BranchOfficeModel
from sqlalchemy import func

class DepositClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, rol_id=None, rut=None, branch_office_id=None, status_id=None, since=None, until=None, page=0, items_per_page=10):
        try:
            if rol_id == 1 or rol_id == 2:
                # Inicialización de filtros dinámicos
                filters = []
                if branch_office_id is not None:
                    filters.append(DepositModel.branch_office_id == branch_office_id)
                if status_id is not None:
                    filters.append(DepositModel.status_id == status_id)
                if since is not None:
                    filters.append(DepositModel.added_date >= since)
                if until is not None:
                    filters.append(DepositModel.added_date <= until)

                # Definir la prioridad de orden para status_id
                status_order = case(
                    (DepositModel.status_id == 1, 1),
                    (DepositModel.status_id == 3, 2),
                    (DepositModel.status_id == 6, 3),
                    else_=4  # Otros valores de status_id van al final
                )

                # Construir la consulta base con los filtros aplicados
                query = self.db.query(
                    DepositModel.id, 
                    DepositModel.branch_office_id, 
                    DepositModel.payment_type_id, 
                    DepositModel.collection_id,
                    DepositModel.status_id,
                    DepositModel.deposited_amount,   
                    DepositModel.payment_number, 
                    DepositModel.collection_amount,
                    func.date_format(DepositModel.collection_date, '%d-%m-%Y').label('collection_date'),
                    BranchOfficeModel.branch_office
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == DepositModel.branch_office_id
                ).filter(
                    *filters
                ).order_by(
                    status_order,  # Primero ordenamos por prioridad de status_id
                    DepositModel.id.desc()  # Luego, ordenamos por ID dentro de cada grupo
                )
            else:
                # Inicialización de filtros dinámicos
                filters = []
                if branch_office_id is not None:
                    filters.append(DepositModel.branch_office_id == branch_office_id)
                if status_id is not None:
                    filters.append(DepositModel.status_id == status_id)
                if since is not None:
                    filters.append(DepositModel.added_date >= since)
                if until is not None:
                    filters.append(DepositModel.added_date <= until)

                # Definir la prioridad de orden para status_id
                status_order = case(
                    (DepositModel.status_id == 1, 1),
                    (DepositModel.status_id == 3, 2),
                    (DepositModel.status_id == 6, 3),
                    else_=4  # Otros valores de status_id van al final
                )

                # Construir la consulta base con los filtros aplicados
                query = self.db.query(
                    DepositModel.id, 
                    DepositModel.branch_office_id, 
                    DepositModel.payment_type_id, 
                    DepositModel.collection_id,
                    DepositModel.status_id,
                    DepositModel.deposited_amount,   
                    DepositModel.payment_number, 
                    DepositModel.collection_amount,
                    func.date_format(DepositModel.collection_date, '%d-%m-%Y').label('collection_date'),
                    BranchOfficeModel.branch_office
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == DepositModel.branch_office_id
                ).filter(
                    BranchOfficeModel.principal_supervisor == rut
                ).filter(
                    *filters
                ).order_by(
                    status_order,  # Primero ordenamos por prioridad de status_id
                    DepositModel.id.desc()  # Luego, ordenamos por ID dentro de cada grupo
                )
                
            # Si se solicita paginación
            if page > 0:
                total_items = query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

            else:
                data = query.all()

            # Serializar los datos
            serialized_data = [{
                "id": deposit.id,
                "branch_office_id": deposit.branch_office_id,
                "payment_type_id": deposit.payment_type_id,
                "collection_id": deposit.collection_id,
                "status_id": deposit.status_id,
                "deposited_amount": deposit.deposited_amount,
                "payment_number": deposit.payment_number,
                "collection_amount": deposit.collection_amount,
                "collection_date": deposit.collection_date,
                "branch_office": deposit.branch_office
            } for deposit in data]

            if page > 0:
                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }
            else:
                return serialized_data

        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    def get(self, id):
        try:
            data_query = self.db.query(
                        DepositModel.id, 
                        DepositModel.branch_office_id, 
                        DepositModel.payment_type_id, 
                        DepositModel.collection_id,
                        DepositModel.status_id,
                        DepositModel.deposited_amount,   
                        DepositModel.payment_number, 
                        DepositModel.collection_amount,
                        DepositModel.collection_date, 
                        BranchOfficeModel.branch_office,
                        DepositModel.added_date,
                        DepositModel.support
                        ). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == DepositModel.branch_office_id). \
                        filter(DepositModel.id == id). \
                        first()

            if data_query:
                # Serializar los datos del empleado
                patent_data = {
                    "id": data_query.id,
                    "branch_office_id": data_query.branch_office_id,
                    "payment_type_id": data_query.payment_type_id,
                    "collection_id": data_query.collection_id,
                    "status_id": data_query.status_id,
                    "deposited_amount": data_query.deposited_amount,
                    "payment_number": data_query.payment_number,
                    "collection_amount": data_query.collection_amount,
                    "collection_date": data_query.collection_date.strftime('%d-%m-%Y'),
                    "branch_office": data_query.branch_office,
                    "added_date": data_query.added_date.strftime('%d-%m-%Y'),
                    "support": data_query.support
                }

                # Crear el resultado final como un diccionario
                result = {
                    "deposit_data": patent_data
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
        deposit = DepositModel()
        
        # Asignar los valores del formulario a la instancia del modelo
        deposit.branch_office_id = form_data.branch_office_id
        deposit.payment_type_id = form_data.payment_type_id
        deposit.collection_id = form_data.collection_id
        deposit.status_id = 1
        deposit.deposited_amount = form_data.deposited_amount
        deposit.payment_number = form_data.payment_number
        deposit.collection_amount = form_data.collection_amount
        deposit.collection_date = form_data.collection_date
        deposit.support = support
        deposit.added_date = datetime.now()

        # Añadir la nueva instancia a la base de datos
        self.db.add(deposit)

        # Intentar hacer commit y manejar posibles errores
        try:
            self.db.commit()
            return {"status": "success", "message": "Deposit saved successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def accept(self, id):
        """
        Actualiza los datos de la patente en la base de datos.
        """
        deposit = self.db.query(DepositModel).filter(DepositModel.id == id).first()
        if not deposit:
            raise HTTPException(status_code=404, detail="Patente no encontrada")

        # Actualizar campos
        deposit.status_id = 6

        self.db.commit()
        self.db.refresh(deposit)

    def reject(self, id):
        """
        Actualiza los datos de la patente en la base de datos.
        """
        deposit = self.db.query(DepositModel).filter(DepositModel.id == id).first()
        if not deposit:
            raise HTTPException(status_code=404, detail="Patente no encontrada")

        # Actualizar campos
        deposit.status_id = 3

        self.db.commit()
        self.db.refresh(deposit)

    def update(self, id, form_data, support_file = None):
        """
        Actualiza los datos de la patente en la base de datos.
        """
        patent = self.db.query(PatentModel).filter(PatentModel.id == id).first()
        if not patent:
            raise HTTPException(status_code=404, detail="Patente no encontrada")

        # Actualizar campos
        patent.branch_office_id = form_data.branch_office_id
        patent.semester = form_data.semester
        patent.year = form_data.year
        if support_file != None:
            patent.support = support_file

        self.db.commit()
        self.db.refresh(patent)

    def delete(self, id):
        try:
            self.db.query(DepositModel).filter(DepositModel.id == id).delete()
            self.db.commit()

            return {"status": "success", "message": "Deposit deleted successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        