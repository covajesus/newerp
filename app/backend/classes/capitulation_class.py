from datetime import datetime
from sqlalchemy.orm import Session
from app.backend.db.models import BranchOfficeModel, CapitulationModel, ExpenseTypeModel, UserModel, TotalAcceptedCapitulations
from app.backend.classes.whatsapp_class import WhatsappClass
from app.backend.classes.helper_class import HelperClass
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import aliased
import requests
import json
from sqlalchemy import cast, String, case, or_

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
                    CapitulationModel.document_date.desc()
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
                    CapitulationModel.document_date.desc()
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
                    CapitulationModel.document_date.desc()
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
                    "payment_support": data_query.payment_support,
                    "why_was_rejected": data_query.why_was_rejected
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

                url = f"https://libredte.cl/api/lce/lce_asientos/crear/" + "76063822"

                response = requests.post(
                    url,
                    json=data,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )

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
                    
                    url = f"https://libredte.cl/api/lce/lce_asientos/crear/" + "76063822"
                    
                    response = requests.post(
                        url,
                        json=data,
                        headers={
                            "Authorization": f"Bearer {TOKEN}",
                            "Content-Type": "application/json",
                        },
                    )
                    
                    # Verificar si la respuesta fue exitosa
                    if response.status_code not in [200, 201]:
                        errors.append({
                            "capitulation_id": capitulation.id,
                            "error": f"Error al crear asiento contable: {response.status_code} - {response.text}"
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
                    
                    url = f"https://libredte.cl/api/lce/lce_asientos/crear/" + "76063822"
                    
                    response = requests.post(
                        url,
                        json=data,
                        headers={
                            "Authorization": f"Bearer {TOKEN}",
                            "Content-Type": "application/json",
                        },
                    )
                    
                    # Verificar si la respuesta fue exitosa
                    if response.status_code not in [200, 201]:
                        errors.append({
                            "capitulation_id": capitulation.id,
                            "error": f"Error al crear asiento contable: {response.status_code} - {response.text}"
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
                    
                    url = f"https://libredte.cl/api/lce/lce_asientos/crear/" + "76063822"
                    
                    response = requests.post(
                        url,
                        json=data,
                        headers={
                            "Authorization": f"Bearer {TOKEN}",
                            "Content-Type": "application/json",
                        },
                    )
                    
                    # Verificar si la respuesta fue exitosa
                    if response.status_code not in [200, 201]:
                        errors.append({
                            "capitulation_id": capitulation.id,
                            "error": f"Error al crear asiento contable: {response.status_code} - {response.text}"
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
