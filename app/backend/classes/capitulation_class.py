from datetime import datetime
from sqlalchemy.orm import Session
from app.backend.db.models import BranchOfficeModel, CapitulationModel, ExpenseTypeModel, UserModel, TotalAcceptedCapitulations, CapitulationBankAccountModel
from app.backend.classes.whatsapp_class import WhatsappClass
from app.backend.classes.helper_class import HelperClass
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import aliased
import requests
import json
from sqlalchemy import cast, String, case, or_, func, and_, extract
from app.backend.classes.accounting_entry_class import AccountingEntryClass

class CapitulationClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, rol_id=None, rut=None, page=0, items_per_page=10, branch_office_id=None, status_id=None):
        try:
            if rol_id == 1 or rol_id == 2:
                # Inicialización de filtros dinámicos
                filters = []
                
                # Agregar filtros opcionales
                if branch_office_id is not None:
                    filters.append(CapitulationModel.branch_office_id == branch_office_id)
                
                if status_id is not None:
                    filters.append(CapitulationModel.status_id == status_id)
                
                # No mostrar rechazadas
                filters.append(CapitulationModel.status_id != 3)

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
                    case(
                        (CapitulationModel.status_id == 1, 0),   # No Revisado
                        (CapitulationModel.status_id == 2, 1),   # Aceptado
                        (CapitulationModel.status_id == 13, 2),  # Pagada
                        (CapitulationModel.status_id == 5, 3),   # Imputada Pagada
                        else_=100
                    ),
                    CapitulationModel.id.desc()
                )
            elif rol_id == 5:
                # Inicialización de filtros dinámicos
                filters = []
                
                # Agregar filtros opcionales
                if branch_office_id is not None:
                    filters.append(CapitulationModel.branch_office_id == branch_office_id)
                
                if status_id is not None:
                    filters.append(CapitulationModel.status_id == status_id)
                
                # No mostrar rechazadas
                filters.append(CapitulationModel.status_id != 3)

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
                    UserModel.rut == rut,
                ).filter(
                    *filters
                ).order_by(
                    case(
                        (CapitulationModel.status_id == 1, 0),   # No Revisado
                        (CapitulationModel.status_id == 2, 1),   # Aceptado
                        (CapitulationModel.status_id == 13, 2),  # Pagada
                        (CapitulationModel.status_id == 5, 3),   # Imputada Pagada
                        else_=100
                    ),
                    CapitulationModel.id.desc()
                )   
            else:
                # Inicialización de filtros dinámicos
                filters = []
                
                # Agregar filtros opcionales
                if branch_office_id is not None:
                    filters.append(CapitulationModel.branch_office_id == branch_office_id)
                
                if status_id is not None:
                    filters.append(CapitulationModel.status_id == status_id)
                
                # No mostrar rechazadas
                filters.append(CapitulationModel.status_id != 3)

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
                    case(
                        (CapitulationModel.status_id == 1, 0),   # No Revisado
                        (CapitulationModel.status_id == 2, 1),   # Aceptado
                        (CapitulationModel.status_id == 13, 2),  # Pagada
                        (CapitulationModel.status_id == 5, 3),   # Imputada Pagada
                        else_=100
                    ),
                    CapitulationModel.id.desc()
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
                    "document_date": capitulation.document_date.strftime("%d-%m-%Y"),
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
                    "document_date": capitulation.document_date.strftime("%d-%m-%Y"),
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
                CapitulationModel.id.desc()
            )

            data = query.all()

            serialized_data = [{
                    "id": capitulation.id,
                    "document_date": capitulation.document_date.strftime("%d-%m-%Y"),
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
        
    def total_accepted_capitulations(self, rut=None):
        try:
            query = self.db.query(
                TotalAcceptedCapitulations.rut,
                TotalAcceptedCapitulations.full_name,
                TotalAcceptedCapitulations.amount
            )

            # Si se proporciona un RUT, filtrar por él
            if rut:
                query = query.filter(TotalAcceptedCapitulations.rut == rut)

            query = query.order_by(TotalAcceptedCapitulations.rut)

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
                CapitulationModel.user_rut,
                UserModel.id.label("user_id"),
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
                CapitulationModel.why_was_rejected,
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
                bank_account = None
                if getattr(data_query, "user_id", None) is not None:
                    bank_account = (
                        self.db.query(CapitulationBankAccountModel)
                        .filter(CapitulationBankAccountModel.user_id == data_query.user_id)
                        .first()
                    )
                if not bank_account and data_query.user_rut is not None:
                    bank_account = (
                        self.db.query(CapitulationBankAccountModel)
                        .filter(CapitulationBankAccountModel.identification_number == str(data_query.user_rut))
                        .first()
                    )

                # Serializar los datos del empleado
                capitulation_data = {
                    "id": data_query.id,
                    "document_date": data_query.document_date.strftime("%Y-%m-%d") if isinstance(data_query.document_date, datetime) else data_query.document_date,
                    "supplier_rut": data_query.supplier_rut,
                    "user_rut": data_query.user_rut,
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
                    "payment_support": data_query.payment_support,
                    "why_was_rejected": data_query.why_was_rejected
                }

                bank_account_data = None
                if bank_account:
                    bank_account_data = {
                        "id": bank_account.id,
                        "bank_id": bank_account.bank_id,
                        "account_type_id": bank_account.account_type_id,
                        "account_number": bank_account.account_number,
                        "identification_number": bank_account.identification_number,
                        "email": bank_account.email,
                    }

                result = {
                    "capitulation_data": capitulation_data,
                    "bank_account_data": bank_account_data,
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
        capitulation.added_date = datetime.now()

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
            
            # Enviar notificación de WhatsApp sobre el estado de capitulación
            whatsapp_class = WhatsappClass(self.db)
            whatsapp_class.status_capitulation(capitulation.user_rut, capitulation.amount)
            
            return {"status": "success", "message": "Capitulation paid successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def impute(self, form_data):
        token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        capitulation = self.db.query(CapitulationModel).filter(CapitulationModel.id == form_data.id).first()
        if not capitulation:
            return {"status": "error", "message": "Capitulation not found"}
            
        branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == form_data.branch_office_id).first()
        if not branch_office:
            return {"status": "error", "message": "Branch office not found"}
            
        expense_type = self.db.query(ExpenseTypeModel).filter(ExpenseTypeModel.id == form_data.expense_type_id).first()
        if not expense_type:
            return {"status": "error", "message": "Expense type not found"}
            
        period = form_data.period.split('-')
        utf8_date = '01-' + period[1] + '-' + period[0]

        # Actualizar la capitulación con los nuevos valores del formulario
        capitulation.branch_office_id = form_data.branch_office_id
        capitulation.expense_type_id = form_data.expense_type_id
        capitulation.period = period[1] + '-' + period[0]
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

                result = AccountingEntryClass(self.db).create(data, token=token)

                if result.get("status") in ("success", "partial"):
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

            WhatsappClass(self.db).reject_capitulation(capitulation.id)

        capitulation.updated_date = datetime.now()

        self.db.commit()
        self.db.refresh(capitulation)

    def massive_accountability(self):
        """
        Crea asientos contables masivos para todas las capitulaciones con document_date
        entre 2025-12-01 y 2025-12-31.
        Recorre toda la tabla capitulations y genera un asiento contable para cada una,
        similar al método impute pero procesando todos los registros de una vez.
        """
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
        
        # Buscar todas las capitulaciones con document_date entre 2025-12-01 y 2025-12-31
        from datetime import date
        start_date = date(2025, 12, 1)
        end_date = date(2025, 12, 31)
        
        capitulations = self.db.query(CapitulationModel).filter(
            CapitulationModel.document_date >= start_date.strftime('%Y-%m-%d'),
            CapitulationModel.document_date <= end_date.strftime('%Y-%m-%d')
        ).all()
        
        if not capitulations:
            return {
                "status": "success",
                "message": "No se encontraron capitulaciones con document_date entre 2025-12-01 y 2025-12-31",
                "processed": 0,
                "errors": []
            }
        
        processed = 0
        errors = []
        period = "2025-12"
        utf8_date = '01-12-2025'
        
        for capitulation in capitulations:
            try:
                branch_office = self.db.query(BranchOfficeModel).filter(
                    BranchOfficeModel.id == capitulation.branch_office_id
                ).first()
                
                if not branch_office:
                    errors.append({
                        "capitulation_id": capitulation.id,
                        "error": "No se encontró la sucursal asociada"
                    })
                    continue
                
                expense_type = self.db.query(ExpenseTypeModel).filter(
                    ExpenseTypeModel.id == capitulation.expense_type_id
                ).first()
                
                if not expense_type:
                    errors.append({
                        "capitulation_id": capitulation.id,
                        "error": "No se encontró el tipo de gasto asociado"
                    })
                    continue
                
                # Solo crear asiento contable si document_type_id == 39
                if capitulation.document_type_id == 39:
                    gloss = (
                        branch_office.branch_office
                        + "_"
                        + str(expense_type.accounting_account)
                        + "_"
                        + utf8_date
                        + "_Rendicion_"
                        + str(capitulation.id)
                    )
                    
                    data = {
                        "fecha": period + "-01",
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
                    
                    result = AccountingEntryClass(self.db).create(data, token=TOKEN)
                    
                    # Verificar si la respuesta fue exitosa
                    if result.get("status") not in ("success", "partial"):
                        errors.append({
                            "capitulation_id": capitulation.id,
                            "error": f"Error al crear asiento contable: {result.get('status')} - {result.get('errors') or result}"
                        })
                        continue
                
                # Actualizar la capitulación: status_id = 5 y period = "2025-12"
                capitulation.status_id = 5
                capitulation.period = period
                capitulation.updated_date = datetime.now()
                
                self.db.add(capitulation)
                processed += 1
                
            except Exception as e:
                errors.append({
                    "capitulation_id": capitulation.id,
                    "error": f"Error al procesar capitulación: {str(e)}"
                })
                continue
        
        # Hacer commit de todos los cambios
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            return {
                "status": "error",
                "message": f"Error al guardar cambios en la base de datos: {str(e)}",
                "processed": processed,
                "errors": errors
            }
        
        return {
            "status": "success",
            "message": f"Procesamiento masivo completado. {processed} capitulaciones procesadas exitosamente.",
            "processed": processed,
            "total_found": len(capitulations),
            "errors": errors
        }

    def massive_impute_status_13(self):
        """
        Crea asientos contables masivos para todas las capitulaciones con status_id = 13.
        El periodo se extrae del document_date de cada capitulación.
        Recorre toda la tabla capitulations y genera un asiento contable para cada una,
        similar al proceso de imputación individual pero procesando todos los registros de una vez.
        """
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
        
        # Buscar todas las capitulaciones con status_id = 13
        capitulations = self.db.query(CapitulationModel).filter(
            CapitulationModel.status_id == 13
        ).all()
        
        if not capitulations:
            return {
                "status": "success",
                "message": "No se encontraron capitulaciones con status_id = 13 para procesar",
                "processed": 0,
                "errors": []
            }
        
        processed = 0
        errors = []
        
        for capitulation in capitulations:
            try:
                # Validar que tenga los datos necesarios
                if not capitulation.branch_office_id:
                    errors.append({
                        "capitulation_id": capitulation.id,
                        "error": "No tiene branch_office_id asignado"
                    })
                    continue
                
                if not capitulation.expense_type_id:
                    errors.append({
                        "capitulation_id": capitulation.id,
                        "error": "No tiene expense_type_id asignado"
                    })
                    continue
                
                if not capitulation.document_date:
                    errors.append({
                        "capitulation_id": capitulation.id,
                        "error": "No tiene document_date asignado"
                    })
                    continue
                
                branch_office = self.db.query(BranchOfficeModel).filter(
                    BranchOfficeModel.id == capitulation.branch_office_id
                ).first()
                
                if not branch_office:
                    errors.append({
                        "capitulation_id": capitulation.id,
                        "error": "No se encontró la sucursal asociada"
                    })
                    continue
                
                expense_type = self.db.query(ExpenseTypeModel).filter(
                    ExpenseTypeModel.id == capitulation.expense_type_id
                ).first()
                
                if not expense_type:
                    errors.append({
                        "capitulation_id": capitulation.id,
                        "error": "No se encontró el tipo de gasto asociado"
                    })
                    continue
                
                # Extraer el periodo del document_date
                if isinstance(capitulation.document_date, datetime):
                    period = capitulation.document_date.strftime('%Y-%m')
                elif isinstance(capitulation.document_date, str):
                    # Si es string, intentar parsearlo
                    try:
                        date_obj = datetime.strptime(capitulation.document_date, '%Y-%m-%d')
                        period = date_obj.strftime('%Y-%m')
                    except ValueError:
                        try:
                            date_obj = datetime.strptime(capitulation.document_date, '%Y-%m-%d %H:%M:%S')
                            period = date_obj.strftime('%Y-%m')
                        except ValueError:
                            errors.append({
                                "capitulation_id": capitulation.id,
                                "error": f"Formato de fecha inválido: {capitulation.document_date}"
                            })
                            continue
                else:
                    errors.append({
                        "capitulation_id": capitulation.id,
                        "error": f"Tipo de fecha no soportado: {type(capitulation.document_date)}"
                    })
                    continue
                
                # Convertir periodo para utf8_date (formato DD-MM-YYYY)
                period_parts = period.split('-')
                utf8_date = '01-' + period_parts[1] + '-' + period_parts[0]
                
                # Solo crear asiento contable si document_type_id == 39
                if capitulation.document_type_id == 39:
                    gloss = (
                        branch_office.branch_office
                        + "_"
                        + str(expense_type.accounting_account)
                        + "_"
                        + utf8_date
                        + "_Rendicion_"
                        + str(capitulation.id)
                    )
                    
                    data = {
                        "fecha": period + "-01",
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
                    
                    result = AccountingEntryClass(self.db).create(data, token=TOKEN)
                    
                    # Verificar si la respuesta fue exitosa
                    if result.get("status") not in ("success", "partial"):
                        errors.append({
                            "capitulation_id": capitulation.id,
                            "error": f"Error al crear asiento contable: {result.get('status')} - {result.get('errors') or result}"
                        })
                        continue
                
                # Actualizar la capitulación: status_id = 5 y period extraído del document_date
                capitulation.status_id = 5
                capitulation.period = period_parts[1] + '-' + period_parts[0]  # Formato MM-YYYY
                capitulation.updated_date = datetime.now()
                
                self.db.add(capitulation)
                processed += 1
                
            except Exception as e:
                errors.append({
                    "capitulation_id": capitulation.id,
                    "error": f"Error al procesar capitulación: {str(e)}"
                })
                continue
        
        # Hacer commit de todos los cambios
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            return {
                "status": "error",
                "message": f"Error al guardar cambios en la base de datos: {str(e)}",
                "processed": processed,
                "errors": errors
            }
        
        return {
            "status": "success",
            "message": f"Procesamiento masivo completado. {processed} capitulaciones procesadas exitosamente.",
            "processed": processed,
            "total_found": len(capitulations),
            "errors": errors
        }

    def massive_impute(self, period, items):
        """
        Imputa masivamente las capitulaciones seleccionadas.
        Recibe un periodo y una lista de items con id y expense_type_id.
        Para cada capitulación:
        1. Actualiza el expense_type_id
        2. Usa el periodo proporcionado
        3. Envía a LibreDTE (conta) si document_type_id == 39
        4. Actualiza status_id = 5 y period
        
        Args:
            period: String con el periodo en formato 'YYYY-MM'
            items: Lista de diccionarios con 'id' y 'expense_type_id'
        """
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
        
        if not items:
            return {
                "status": "error",
                "message": "No se proporcionaron capitulaciones para procesar",
                "processed": 0,
                "errors": []
            }
        
        # Extraer los IDs de las capitulaciones
        capitulation_ids = [item['id'] if isinstance(item, dict) else item.id for item in items]
        
        # Buscar las capitulaciones por sus IDs
        capitulations = self.db.query(CapitulationModel).filter(
            CapitulationModel.id.in_(capitulation_ids)
        ).all()
        
        if not capitulations:
            return {
                "status": "error",
                "message": "No se encontraron las capitulaciones especificadas",
                "processed": 0,
                "errors": []
            }
        
        # Crear un diccionario para mapear id -> expense_type_id
        expense_type_map = {}
        for item in items:
            item_id = item['id'] if isinstance(item, dict) else item.id
            expense_type_id = item['expense_type_id'] if isinstance(item, dict) else item.expense_type_id
            expense_type_map[item_id] = expense_type_id
        
        processed = 0
        errors = []
        
        for capitulation in capitulations:
            try:
                # Obtener el nuevo expense_type_id del mapa
                new_expense_type_id = expense_type_map.get(capitulation.id)
                if not new_expense_type_id:
                    errors.append({
                        "capitulation_id": capitulation.id,
                        "error": "No se proporcionó expense_type_id para esta capitulación"
                    })
                    continue
                
                # Actualizar el expense_type_id
                capitulation.expense_type_id = new_expense_type_id
                
                # Validar que tenga los datos necesarios
                if not capitulation.branch_office_id:
                    errors.append({
                        "capitulation_id": capitulation.id,
                        "error": "No tiene branch_office_id asignado"
                    })
                    continue
                
                if not capitulation.document_date:
                    errors.append({
                        "capitulation_id": capitulation.id,
                        "error": "No tiene document_date asignado"
                    })
                    continue
                
                branch_office = self.db.query(BranchOfficeModel).filter(
                    BranchOfficeModel.id == capitulation.branch_office_id
                ).first()
                
                if not branch_office:
                    errors.append({
                        "capitulation_id": capitulation.id,
                        "error": "No se encontró la sucursal asociada"
                    })
                    continue
                
                expense_type = self.db.query(ExpenseTypeModel).filter(
                    ExpenseTypeModel.id == new_expense_type_id
                ).first()
                
                if not expense_type:
                    errors.append({
                        "capitulation_id": capitulation.id,
                        "error": f"No se encontró el tipo de gasto con id {new_expense_type_id}"
                    })
                    continue
                
                # Verificar que el expense_type tenga accounting_account
                if not expense_type.accounting_account:
                    errors.append({
                        "capitulation_id": capitulation.id,
                        "error": f"El tipo de gasto {new_expense_type_id} no tiene accounting_account asignado"
                    })
                    continue
                
                # Usar el periodo proporcionado desde el frontend
                # Validar formato del periodo (debe ser YYYY-MM)
                try:
                    period_parts = period.split('-')
                    if len(period_parts) != 2 or len(period_parts[0]) != 4 or len(period_parts[1]) != 2:
                        raise ValueError("Formato de periodo inválido")
                    # Validar que sea un periodo válido
                    year = int(period_parts[0])
                    month = int(period_parts[1])
                    if month < 1 or month > 12:
                        raise ValueError("Mes inválido")
                except (ValueError, IndexError) as e:
                    errors.append({
                        "capitulation_id": capitulation.id,
                        "error": f"Formato de periodo inválido: {period}. Debe ser YYYY-MM"
                    })
                    continue
                
                # Convertir periodo para utf8_date (formato DD-MM-YYYY)
                utf8_date = '01-' + period_parts[1] + '-' + period_parts[0]
                
                # Solo crear asiento contable si document_type_id == 39
                if capitulation.document_type_id == 39:
                    gloss = (
                        branch_office.branch_office
                        + "_"
                        + str(expense_type.accounting_account)
                        + "_"
                        + utf8_date
                        + "_Rendicion_"
                        + str(capitulation.id)
                    )
                    
                    data = {
                        "fecha": period + "-01",
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
                    
                    result = AccountingEntryClass(self.db).create(data, token=TOKEN)
                    
                    # Verificar si la respuesta fue exitosa
                    if result.get("status") not in ("success", "partial"):
                        errors.append({
                            "capitulation_id": capitulation.id,
                            "error": f"Error al crear asiento contable: {result.get('status')} - {result.get('errors') or result}"
                        })
                        # Continuar para actualizar el status aunque falle el envío a LibreDTE
                
                # Actualizar la capitulación: status_id = 5 y period extraído del document_date
                # Esto se hace siempre, independientemente del document_type_id o si falló el envío a LibreDTE
                capitulation.status_id = 5
                capitulation.period = period_parts[1] + '-' + period_parts[0]  # Formato MM-YYYY
                capitulation.updated_date = datetime.now()
                
                self.db.add(capitulation)
                
                # Hacer commit individual para cada capitulación para asegurar que se guarde
                try:
                    self.db.commit()
                    processed += 1
                except Exception as e:
                    self.db.rollback()
                    errors.append({
                        "capitulation_id": capitulation.id,
                        "error": f"Error al guardar cambios en la base de datos: {str(e)}"
                    })
                    continue
                
            except Exception as e:
                errors.append({
                    "capitulation_id": capitulation.id,
                    "error": f"Error al procesar capitulación: {str(e)}"
                })
                self.db.rollback()
                continue
        
        return {
            "status": "success",
            "message": f"Imputación masiva completada. {processed} capitulaciones imputadas exitosamente.",
            "processed": processed,
            "total_found": len(capitulations),
            "errors": errors
        }

    @staticmethod
    def _payment_month_filter(year: int, month: int):
        """
        Filtra estrictamente por mes/año de payment_date (fecha de pago),
        no por document_date / added_date / period (fecha de carga o imputación).
        Soporta YYYY-MM-DD, DD-MM-YYYY y DD/MM/YYYY.
        """
        y = int(year)
        m = int(month)
        ym = f"{y:04d}-{m:02d}"
        y_str = f"{y:04d}"
        m_str = f"{m:02d}"

        # Formato principal en BD: YYYY-MM-DD (ej. 2026-08-05)
        ymd_prefix = CapitulationModel.payment_date.like(f"{ym}-%")
        ymd_exact_month = and_(
            func.substr(CapitulationModel.payment_date, 1, 4) == y_str,
            func.substr(CapitulationModel.payment_date, 6, 2) == m_str,
            func.substr(CapitulationModel.payment_date, 5, 1) == "-",
        )

        # Alternativos: DD-MM-YYYY / DD/MM/YYYY
        dmy_slash = CapitulationModel.payment_date.like(f"%/{m_str}/{y_str}")
        dmy_dash = CapitulationModel.payment_date.like(f"%-{m_str}-{y_str}")

        return or_(ymd_prefix, ymd_exact_month, dmy_slash, dmy_dash)

    @staticmethod
    def _document_month_filter(year: int, month: int):
        """Filtra estrictamente por mes/año de document_date (DATE)."""
        y = int(year)
        m = int(month)
        if m < 1 or m > 12:
            return None
        doc = CapitulationModel.document_date
        return and_(extract("year", doc) == y, extract("month", doc) == m)

    @staticmethod
    def _fmt_doc_date(value):
        if value is None:
            return ""
        if hasattr(value, "strftime"):
            return value.strftime("%d-%m-%Y")
        raw = str(value).strip().split(" ")[0]
        if len(raw) >= 10 and raw[4] == "-" and raw[7] == "-":
            return f"{raw[8:10]}-{raw[5:7]}-{raw[0:4]}"
        return raw

    def report_paid_summary(
        self,
        supervisor_rut: str,
        year: int,
        month: int,
        date_type: str = "payment",
        document_year: int = None,
        document_month: int = None,
    ):
        """
        Informe de rendiciones pagadas, siempre totalizado por lote de pago
        (beneficiario + payment_date + payment_number).
        date_type elige qué fecha usa el mes/año:
          - payment: payment_date
          - document: document_date
        """
        try:
            if not supervisor_rut or not year or not month:
                return {"status": "error", "message": "supervisor_rut, year y month son obligatorios"}
            if month < 1 or month > 12:
                return {"status": "error", "message": "month inválido"}

            date_type = (date_type or "payment").strip().lower()
            if date_type not in ("payment", "document"):
                return {"status": "error", "message": "date_type debe ser payment o document"}

            if document_year and document_month:
                date_type = "document"
                year = int(document_year)
                month = int(document_month)

            filters = [
                BranchOfficeModel.principal_supervisor == supervisor_rut,
                CapitulationModel.status_id.in_([5, 13]),
                CapitulationModel.payment_date.isnot(None),
                CapitulationModel.payment_date != "",
            ]

            if date_type == "document":
                doc_filter = self._document_month_filter(int(year), int(month))
                if doc_filter is None:
                    return {"status": "error", "message": "month inválido"}
                filters.append(doc_filter)
            else:
                filters.append(self._payment_month_filter(year, month))

            rows = (
                self.db.query(
                    CapitulationModel.user_rut,
                    UserModel.full_name,
                    CapitulationModel.payment_date,
                    CapitulationModel.payment_number,
                    func.sum(CapitulationModel.amount).label("total"),
                    func.count(CapitulationModel.id).label("items_count"),
                )
                .outerjoin(
                    BranchOfficeModel,
                    BranchOfficeModel.id == CapitulationModel.branch_office_id,
                )
                .outerjoin(UserModel, UserModel.rut == CapitulationModel.user_rut)
                .filter(*filters)
                .group_by(
                    CapitulationModel.user_rut,
                    UserModel.full_name,
                    CapitulationModel.payment_date,
                    CapitulationModel.payment_number,
                )
                .order_by(
                    CapitulationModel.payment_date.desc(),
                    UserModel.full_name.asc(),
                )
                .all()
            )

            data = [
                {
                    "user_rut": row.user_rut,
                    "full_name": row.full_name or row.user_rut or "",
                    "payment_date": row.payment_date,
                    "payment_number": row.payment_number or "",
                    "total": int(row.total or 0),
                    "items_count": int(row.items_count or 0),
                }
                for row in rows
            ]
            return {
                "status": "success",
                "data": data,
                "total_amount": sum(item["total"] for item in data),
                "total_payments": len(data),
                "date_type": date_type,
                "view_mode": "payments",
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def report_paid_detail(
        self,
        supervisor_rut: str,
        year: int,
        month: int,
        user_rut: str,
        payment_date: str,
        payment_number: str = "",
        date_type: str = "payment",
        document_year: int = None,
        document_month: int = None,
    ):
        """Detalle de un lote de pago del informe de rendiciones."""
        try:
            if not supervisor_rut or not year or not month or not user_rut or not payment_date:
                return {
                    "status": "error",
                    "message": "supervisor_rut, year, month, user_rut y payment_date son obligatorios",
                }

            date_type = (date_type or "payment").strip().lower()
            if document_year and document_month:
                date_type = "document"
                year = int(document_year)
                month = int(document_month)

            payment_number = payment_number or ""
            number_filter = (
                or_(
                    CapitulationModel.payment_number == payment_number,
                    and_(
                        CapitulationModel.payment_number.is_(None),
                        payment_number == "",
                    ),
                    and_(
                        CapitulationModel.payment_number == "",
                        payment_number == "",
                    ),
                )
                if payment_number == ""
                else (CapitulationModel.payment_number == payment_number)
            )

            filters = [
                BranchOfficeModel.principal_supervisor == supervisor_rut,
                CapitulationModel.status_id.in_([5, 13]),
                CapitulationModel.user_rut == user_rut,
                CapitulationModel.payment_date == payment_date,
                number_filter,
            ]

            if date_type == "document":
                doc_filter = self._document_month_filter(int(year), int(month))
                if doc_filter is not None:
                    filters.append(doc_filter)
            else:
                filters.append(self._payment_month_filter(year, month))

            rows = (
                self.db.query(
                    CapitulationModel.id,
                    CapitulationModel.document_date,
                    CapitulationModel.supplier_rut,
                    CapitulationModel.document_number,
                    CapitulationModel.document_type_id,
                    CapitulationModel.description,
                    CapitulationModel.amount,
                    CapitulationModel.status_id,
                    CapitulationModel.payment_date,
                    CapitulationModel.payment_number,
                    CapitulationModel.payment_support,
                    CapitulationModel.period,
                    CapitulationModel.user_rut,
                    BranchOfficeModel.branch_office,
                    ExpenseTypeModel.expense_type,
                    UserModel.full_name,
                )
                .outerjoin(
                    BranchOfficeModel,
                    BranchOfficeModel.id == CapitulationModel.branch_office_id,
                )
                .outerjoin(
                    ExpenseTypeModel,
                    ExpenseTypeModel.id == CapitulationModel.expense_type_id,
                )
                .outerjoin(UserModel, UserModel.rut == CapitulationModel.user_rut)
                .filter(*filters)
                .order_by(CapitulationModel.id.asc())
                .all()
            )

            def _fmt_doc_date(value):
                if value is None:
                    return ""
                if hasattr(value, "strftime"):
                    return value.strftime("%d-%m-%Y")
                return str(value)

            data = [
                {
                    "id": row.id,
                    "document_date": _fmt_doc_date(row.document_date),
                    "supplier_rut": row.supplier_rut,
                    "document_number": row.document_number,
                    "document_type_id": row.document_type_id,
                    "description": row.description,
                    "amount": int(row.amount or 0),
                    "status_id": row.status_id,
                    "payment_date": row.payment_date,
                    "payment_number": row.payment_number or "",
                    "payment_support": row.payment_support,
                    "period": row.period,
                    "user_rut": row.user_rut,
                    "branch_office": row.branch_office,
                    "expense_type": row.expense_type,
                    "full_name": row.full_name or row.user_rut or "",
                }
                for row in rows
            ]
            return {
                "status": "success",
                "data": data,
                "total_amount": sum(item["amount"] for item in data),
                "items_count": len(data),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
