from sqlalchemy.orm import Session
from app.backend.db.models import DteModel, CustomerModel, BranchOfficeModel
from app.backend.classes.customer_class import CustomerClass
from app.backend.classes.file_class import FileClass
import requests
from datetime import datetime
import json
from sqlalchemy import desc
from sqlalchemy.dialects import mysql
import uuid
import base64
from sqlalchemy import or_
from fastapi import HTTPException

class MachineTicketClass:
    def __init__(self, db: Session):
        self.db = db
        self.file_class = FileClass(db)  # Crear una instancia de FileClass

    def get_all(self, page=0, items_per_page=10):
        try:
            # Inicialización de filtros dinámicos
            filters = []

            filters.append(DteModel.dte_version_id == 1)
            filters.append(DteModel.dte_type_id == 39)
            filters.append(DteModel.rut == None)

            # Construir la consulta base con los filtros aplicados
            query = self.db.query(
                DteModel.id, 
                DteModel.branch_office_id, 
                DteModel.folio, 
                DteModel.total,
                DteModel.added_date,
                DteModel.rut,
                DteModel.entrance_hour,
                DteModel.exit_hour,
                DteModel.status_id,
                DteModel.chip_id,
                CustomerModel.customer,
                BranchOfficeModel.branch_office
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
            ).outerjoin(
                CustomerModel, CustomerModel.rut == DteModel.rut
            ).filter(
                *filters
            ).order_by(
                desc(DteModel.added_date),
                desc(DteModel.rut)
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
                    "id": dte.id,
                    "rut": dte.rut,
                    "branch_office_id": dte.branch_office_id,
                    "customer": dte.customer,
                    "entrance_hour": dte.entrance_hour,
                    "exit_hour": dte.exit_hour,
                    "chip_id": dte.chip_id,
                    "folio": dte.folio,
                    "total": dte.total,
                    "status_id": dte.status_id,
                    "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                    "branch_office": dte.branch_office
                } for dte in data]

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
                    "id": dte.id,
                    "rut": dte.rut,
                    "branch_office_id": dte.branch_office_id,
                    "customer": dte.customer,
                    "entrance_hour": dte.entrance_hour,
                    "exit_hour": dte.exit_hour,
                    "folio": dte.folio,
                    "chip_id": dte.chip_id,
                    "total": dte.total,
                    "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                    "branch_office": dte.branch_office,
                    "status_id": dte.status_id
                } for dte in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}