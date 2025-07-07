from datetime import datetime
from sqlalchemy.orm import Session
from app.backend.db.models import BranchOfficeModel, CapitulationModel, ExpenseTypeModel, UserModel, TotalAcceptedCapitulations
from app.backend.classes.helper_class import HelperClass
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import aliased
import requests
import json
from sqlalchemy import cast, String

class CapitulationClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, rol_id=None, rut=None, page=0, items_per_page=10):
        try:
            if rol_id == 1 or rol_id == 2:
                # Inicialización de filtros dinámicos
                filters = []

                # Construir la consulta base con los filtros aplicados
                query = self.db.query(
                    CapitulationModel.id,
                    CapitulationModel.document_date,
                    CapitulationModel.supplier_rut,
                    CapitulationModel.document_number,
                    CapitulationModel.document_type_id,
                    CapitulationModel.capitulation_type_id,
                    CapitulationModel.branch_office_id,
                    CapitulationModel.expense_type_id,
                    CapitulationModel.description,
                    CapitulationModel.amount,
                    CapitulationModel.support,
                    CapitulationModel.status_id,
                    BranchOfficeModel.id.label("branch_office_id"), 
                    BranchOfficeModel.branch_office,
                    ExpenseTypeModel.id.label("expense_type_id"),
                    ExpenseTypeModel.expense_type,
                    UserModel.full_name,
                    CapitulationModel.payment_date,
                    CapitulationModel.payment_number,
                    CapitulationModel.period,
                    CapitulationModel.payment_support
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == CapitulationModel.branch_office_id
                ).outerjoin(
                    ExpenseTypeModel, ExpenseTypeModel.id == CapitulationModel.expense_type_id
                ).outerjoin(
                    UserModel, UserModel.rut == CapitulationModel.user_rut
                ).filter(
                    *filters
                ).order_by(
                    CapitulationModel.id
                )
            else:
                # Inicialización de filtros dinámicos
                filters = []

                # Construir la consulta base con los filtros aplicados
                query = self.db.query(
                    CapitulationModel.id,
                    CapitulationModel.document_date,
                    CapitulationModel.supplier_rut,
                    CapitulationModel.document_number,
                    CapitulationModel.document_type_id,
                    CapitulationModel.capitulation_type_id,
                    CapitulationModel.branch_office_id,
                    CapitulationModel.expense_type_id,
                    CapitulationModel.description,
                    CapitulationModel.amount,
                    CapitulationModel.support,
                    CapitulationModel.status_id,
                    BranchOfficeModel.id.label("branch_office_id"), 
                    BranchOfficeModel.branch_office,
                    ExpenseTypeModel.id.label("expense_type_id"),
                    ExpenseTypeModel.expense_type,
                    UserModel.full_name,
                    CapitulationModel.payment_date,
                    CapitulationModel.payment_number,
                    CapitulationModel.period,
                    CapitulationModel.payment_support
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == CapitulationModel.branch_office_id
                ).outerjoin(
                    ExpenseTypeModel, ExpenseTypeModel.id == CapitulationModel.expense_type_id
                ).outerjoin(
                    UserModel, UserModel.rut == CapitulationModel.user_rut
                ).filter(
                    BranchOfficeModel.principal_supervisor == rut,
                ).filter(
                    *filters
                ).order_by(
                    CapitulationModel.id
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
                    "id": capitulation.id,
                    "document_date": capitulation.document_date,
                    "supplier_rut": capitulation.supplier_rut,
                    "document_number": capitulation.document_number,
                    "document_type_id": capitulation.document_type_id,
                    "capitulation_type_id": capitulation.capitulation_type_id,
                    "branch_office_id": capitulation.branch_office_id,
                    "branch_office": capitulation.branch_office,
                    "expense_type_id": capitulation.expense_type_id,
                    "expense_type": capitulation.expense_type,
                    "description": capitulation.description,
                    "amount": capitulation.amount,
                    "support": capitulation.support,
                    "full_name": capitulation.full_name,
                    "status_id": capitulation.status_id,
                    "payment_date": capitulation.payment_date,
                    "payment_number": capitulation.payment_number,
                    "period": capitulation.period,
                    "payment_support": capitulation.payment_support
                } for capitulation in data]

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
                    "id": capitulation.id,
                    "document_date": capitulation.document_date,
                    "supplier_rut": capitulation.supplier_rut,
                    "document_number": capitulation.document_number,
                    "document_type_id": capitulation.document_type_id,
                    "capitulation_type_id": capitulation.capitulation_type_id,
                    "branch_office_id": capitulation.branch_office_id,
                    "branch_office": capitulation.branch_office,
                    "expense_type_id": capitulation.expense_type_id,
                    "expense_type": capitulation.expense_type,
                    "description": capitulation.description,
                    "amount": capitulation.amount,
                    "support": capitulation.support,
                    "full_name": capitulation.full_name,
                    "status_id": capitulation.status_id,
                    "payment_date": capitulation.payment_date,
                    "payment_number": capitulation.payment_number,
                    "period": capitulation.period,
                    "payment_support": capitulation.payment_support
                } for capitulation in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
    
    def get_all_accepted(self, rut=None):
        try:
            # Inicialización de filtros dinámicos
            filters = []

            filters.append(CapitulationModel.status_id == 2)
            filters.append(CapitulationModel.user_rut == rut)

            # Construir la consulta base con los filtros aplicados
            query = self.db.query(
                CapitulationModel.id,
                CapitulationModel.document_date,
                CapitulationModel.supplier_rut,
                CapitulationModel.document_number,
                CapitulationModel.document_type_id,
                CapitulationModel.capitulation_type_id,
                CapitulationModel.branch_office_id,
                CapitulationModel.expense_type_id,
                CapitulationModel.description,
                CapitulationModel.amount,
                CapitulationModel.support,
                CapitulationModel.status_id,
                BranchOfficeModel.id.label("branch_office_id"), 
                BranchOfficeModel.branch_office,
                ExpenseTypeModel.id.label("expense_type_id"),
                ExpenseTypeModel.expense_type,
                UserModel.full_name,
                CapitulationModel.payment_date,
                CapitulationModel.payment_number,
                CapitulationModel.period,
                CapitulationModel.payment_support
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == CapitulationModel.branch_office_id
            ).outerjoin(
                ExpenseTypeModel, ExpenseTypeModel.id == CapitulationModel.expense_type_id
            ).outerjoin(
                UserModel, UserModel.rut == CapitulationModel.user_rut
            ).filter(
                *filters
            ).order_by(
                CapitulationModel.id
            )

            data = query.all()

            serialized_data = [{
                    "id": capitulation.id,
                    "document_date": capitulation.document_date,
                    "supplier_rut": capitulation.supplier_rut,
                    "document_number": capitulation.document_number,
                    "document_type_id": capitulation.document_type_id,
                    "capitulation_type_id": capitulation.capitulation_type_id,
                    "branch_office_id": capitulation.branch_office_id,
                    "branch_office": capitulation.branch_office,
                    "expense_type_id": capitulation.expense_type_id,
                    "expense_type": capitulation.expense_type,
                    "description": capitulation.description,
                    "amount": capitulation.amount,
                    "support": capitulation.support,
                    "full_name": capitulation.full_name,
                    "status_id": capitulation.status_id,
                    "payment_date": capitulation.payment_date,
                    "payment_number": capitulation.payment_number,
                    "period": capitulation.period,
                    "payment_support": capitulation.payment_support
            } for capitulation in data]

            return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
        
    def total_accepted_capitulations(self):
        try:
            query = self.db.query(
                TotalAcceptedCapitulations.rut,
                TotalAcceptedCapitulations.full_name,
                TotalAcceptedCapitulations.amount
            ).order_by(
                TotalAcceptedCapitulations.rut
            )

            data = query.all()

            serialized_data = [{
                "rut": capitulation.rut,
                "full_name": capitulation.full_name,
                "amount": capitulation.amount
            } for capitulation in data]

            return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
        
    def get(self, id):
        try:
            data_query = self.db.query(
                CapitulationModel.id,
                cast(CapitulationModel.document_date, String).label("document_date"),
                CapitulationModel.supplier_rut,
                CapitulationModel.document_number,
                CapitulationModel.document_type_id,
                CapitulationModel.capitulation_type_id,
                CapitulationModel.branch_office_id,
                CapitulationModel.expense_type_id,
                CapitulationModel.description,
                CapitulationModel.amount,
                CapitulationModel.support,
                CapitulationModel.status_id,
                BranchOfficeModel.branch_office,
                ExpenseTypeModel.id.label("expense_type_id"),
                ExpenseTypeModel.expense_type,
                UserModel.full_name,
                cast(CapitulationModel.payment_date, String).label("payment_date"),
                CapitulationModel.payment_number,
                CapitulationModel.period,
                CapitulationModel.payment_support
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == CapitulationModel.branch_office_id
            ).outerjoin(
                ExpenseTypeModel, ExpenseTypeModel.id == CapitulationModel.expense_type_id
            ).outerjoin(
                UserModel, UserModel.rut == CapitulationModel.user_rut
            ).filter(
                CapitulationModel.id == id
            ).first()

            if data_query:
                # Serializar los datos del empleado
                capitulation_data = {
                    "id": data_query.id,
                    "document_date": data_query.document_date.strftime("%Y-%m-%d") if isinstance(data_query.document_date, datetime) else data_query.document_date,
                    "supplier_rut": data_query.supplier_rut,
                    "document_number": data_query.document_number,
                    "document_type_id": data_query.document_type_id,
                    "capitulation_type_id": data_query.capitulation_type_id,
                    "branch_office_id": data_query.branch_office_id,
                    "branch_office": data_query.branch_office,
                    "expense_type_id": data_query.expense_type_id,
                    "expense_type": data_query.expense_type,
                    "description": data_query.description,
                    "amount": data_query.amount,
                    "support": data_query.support,
                    "full_name": data_query.full_name,
                    "status_id": data_query.status_id,
                    "payment_date": data_query.payment_date.strftime("%Y-%m-%d") if isinstance(data_query.payment_date, datetime) else data_query.payment_date,
                    "payment_number": data_query.payment_number,
                    "period": f"{data_query.period.split('-')[1]}-{data_query.period.split('-')[0]}" if isinstance(data_query.period, str) and "-" in data_query.period else data_query.period,
                    "payment_support": data_query.payment_support
                }

                result = {
                    "capitulation_data": capitulation_data
                }

                serialized_result = json.dumps(result)

                return serialized_result

            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def store(self, form_data, user_session, support):
        capitulation = CapitulationModel()
        capitulation.document_date = form_data.document_date
        capitulation.status_id = 1
        capitulation.supplier_rut = form_data.supplier_rut
        capitulation.user_rut = user_session.rut
        capitulation.document_number = form_data.document_number
        capitulation.document_type_id = form_data.document_type_id
        capitulation.capitulation_type_id = form_data.capitulation_type_id
        capitulation.branch_office_id = form_data.branch_office_id
        capitulation.expense_type_id = form_data.expense_type_id
        capitulation.description = form_data.description
        capitulation.amount = form_data.amount
        capitulation.support = support

        self.db.add(capitulation)

        try:
            self.db.commit()
            return {"status": "success", "message": "Capitulation saved successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def pay(self, id, form_data, support):
        capitulation = self.db.query(CapitulationModel).filter(CapitulationModel.id == id).first()
        capitulation.payment_date = form_data.payment_date
        capitulation.payment_number = form_data.payment_number
        capitulation.status_id = 13
        capitulation.payment_support = support

        self.db.add(capitulation)

        try:
            self.db.commit()
            return {"status": "success", "message": "Capitulation paid successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def impute(self, form_data):
        token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        capitulation = self.db.query(CapitulationModel).filter(CapitulationModel.id == form_data.id).first()
        branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == capitulation.branch_office_id).first()
        expense_type = self.db.query(ExpenseTypeModel).filter(ExpenseTypeModel.id == capitulation.expense_type_id).first()
        period = form_data.period.split('-')
        utf8_date = '01-' + period[1] + '-' + period[0]

        capitulation.period =  period[1] + '-' + period[0]
        capitulation.status_id = 5

        self.db.add(capitulation)

        try:
            self.db.commit()

            if capitulation.document_type_id == 39:
                gloss = (
                    branch_office.branch_office
                    + "_"
                    + expense_type.accounting_account
                    + "_"
                    + utf8_date
                    + "_Rendicion_"
                    + str(capitulation.id)
                )

                data = {
                    "fecha": form_data.period + "-01",
                    "glosa": gloss,
                    "detalle": {
                        'debe': {
                           str(expense_type.accounting_account): capitulation.amount,
                        },
                        'haber': {
                            '111000101': capitulation.amount,
                        }
                    },
                    "operacion": "I",
                    "documentos": {
                        "emitidos": [
                            {
                                "dte": '',
                                "folio": 0,
                            }
                        ]
                    },
                }

                print(data)

                url = f"https://libredte.cl/api/lce/lce_asientos/crear/" + "76063822"

                response = requests.post(
                    url,
                    json=data,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )

                print(response.text)

                if response.status_code == 200:
                    return {"status": "success", "message": "Capitulation imputed successfully"}
            else:
                return {"status": "success", "message": "Capitulation imputed successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def delete(self, id):
        try:
            self.db.query(CapitulationModel).filter(CapitulationModel.id == id).delete()
            self.db.commit()

            return {"status": "success", "message": "Capitulation deleted successfully"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def update(self, form_data):
        capitulation = self.db.query(CapitulationModel).filter(CapitulationModel.id == form_data.id).first()

        if not capitulation:
            raise HTTPException(status_code=404, detail="Rendición no encontrada")

        if form_data.question == '1':
            capitulation.status_id = 2
        else:
            capitulation.status_id = 3
            capitulation.why_was_rejected = form_data.why_was_rejected

        capitulation.updated_date = datetime.now()

        self.db.commit()
        self.db.refresh(capitulation)

