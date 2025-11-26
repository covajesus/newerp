from datetime import datetime
from sqlalchemy.orm import Session
from app.backend.db.models import BranchOfficeModel, PatentModel, CashReserveModel, CashierModel
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import aliased
import json
from sqlalchemy import func

class CashReserveClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, branch_office_id=None, page=0, items_per_page=10):
        try:
        
            filters = []
            if branch_office_id is not None:
                filters.append(CashReserveModel.branch_office_id == branch_office_id)
         
            query = self.db.query(
                CashReserveModel.id, 
                CashReserveModel.branch_office_id, 
                CashReserveModel.cashier_id,
                CashierModel.cashier,
                CashReserveModel.amount,
                BranchOfficeModel.branch_office,
                func.date_format(CashReserveModel.added_date, '%d-%m-%Y').label('added_date')
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == CashReserveModel.branch_office_id
            ).outerjoin(
                CashierModel, CashierModel.id == CashReserveModel.cashier_id
            ).filter(
                *filters
            ).order_by(
                CashReserveModel.id
            )

            if page > 0:
                total_items = query.count()
                total_pages = (total_items + items_per_page - 1)

                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                # Serializar los datos
                serialized_data = [{
                    "id": cash_reserve.id,
                    "branch_office_id": cash_reserve.branch_office_id,
                    "cashier_id": cash_reserve.cashier_id,
                    "cashier": cash_reserve.cashier,
                    "amount": cash_reserve.amount,
                    "branch_office": cash_reserve.branch_office,
                    "added_date": cash_reserve.added_date
                } for cash_reserve in data]

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
                    "id": cash_reserve.id,
                    "branch_office_id": cash_reserve.branch_office_id,
                    "cashier_id": cash_reserve.cashier_id,
                    "cashier": cash_reserve.cashier,
                    "amount": cash_reserve.amount,
                    "branch_office": cash_reserve.branch_office,
                    "added_date": cash_reserve.added_date
                } for cash_reserve in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
              
    def get(self, id):
        try:
            data_query = self.db.query(PatentModel.id, PatentModel.semester, PatentModel.year, PatentModel.support, BranchOfficeModel.id.label("branch_office_id"), BranchOfficeModel.branch_office). \
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
                    "semester": data_query.semester,
                    "year": data_query.year,
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

    def store(self, form_data):
        cash_reserve = CashReserveModel()
        cash_reserve.branch_office_id = form_data.branch_office_id
        cash_reserve.cashier_id = form_data.cashier_id
        cash_reserve.amount = form_data.amount
        cash_reserve.added_date = datetime.now()

        self.db.add(cash_reserve)

        try:
            self.db.commit()
            return {"status": "success", "message": "Cash reserve saved successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def delete(self, id):
        try:
            self.db.query(CashReserveModel).filter(CashReserveModel.id == id).delete()
            self.db.commit()

            return {"status": "success", "message": "Cash reserve deleted successfully"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def update(self, id, form_data, support_file = None):
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

