from sqlalchemy.orm import Session
from app.backend.db.models import DteModel, CustomerModel, BranchOfficeModel, UserModel, ExpenseTypeModel, SupplierModel
from app.backend.classes.customer_class import CustomerClass
from app.backend.classes.helper_class import HelperClass
from app.backend.classes.file_class import FileClass
from sqlalchemy import desc
from sqlalchemy.dialects import mysql
from sqlalchemy import or_
from datetime import datetime
from fastapi import HTTPException
import requests
import json
import base64
import uuid
from sqlalchemy.sql import func

class CustomerTicketBillClass:
    def __init__(self, db: Session):
        self.db = db
        self.file_class = FileClass(db)  # Crear una instancia de FileClass

    def get_all(self, rol_id = None, rut = None, page=1, items_per_page=10):
        try:

            if rol_id == 1 or rol_id == 2:
                # Inicialización de filtros dinámicos
                filters = []

                filters.append(DteModel.dte_version_id == 1)
                filters.append(DteModel.status_id > 3)
                filters.append(DteModel.status_id < 16)
                filters.append(DteModel.rut != None)
                filters.append(DteModel.rut != '66666666-6')
                filters.append(or_(DteModel.dte_type_id == 33, DteModel.dte_type_id == 39))

                # Construir la consulta base con los filtros aplicados
                query = self.db.query(
                        DteModel.id, 
                        DteModel.branch_office_id, 
                        DteModel.dte_type_id, 
                        DteModel.folio, 
                        DteModel.total,
                        DteModel.added_date,
                        DteModel.rut,
                        DteModel.status_id,
                        DteModel.chip_id,
                        DteModel.payment_date,
                        BranchOfficeModel.branch_office,
                        CustomerModel.customer.label('customer')
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
                ).outerjoin(
                    CustomerModel, CustomerModel.rut == DteModel.rut
                ).filter(
                    *filters
                ).order_by(
                    DteModel.added_date.desc()
                )
            elif rol_id == 4:
                                # Inicialización de filtros dinámicos
                filters = []

                filters.append(DteModel.dte_version_id == 1)
                filters.append(DteModel.status_id > 3)
                filters.append(DteModel.status_id < 16)
                filters.append(DteModel.rut != None)
                filters.append(DteModel.rut != '66666666-6')
                filters.append(or_(DteModel.dte_type_id == 33, DteModel.dte_type_id == 39))

                # Construir la consulta base con los filtros aplicados
                query = self.db.query(
                        DteModel.id, 
                        DteModel.branch_office_id, 
                        DteModel.dte_type_id, 
                        DteModel.folio, 
                        DteModel.total,
                        DteModel.added_date,
                        DteModel.rut,
                        DteModel.status_id,
                        DteModel.payment_date,
                        DteModel.chip_id,
                        BranchOfficeModel.branch_office,
                        CustomerModel.customer.label('customer')
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
                ).outerjoin(
                    CustomerModel, CustomerModel.rut == DteModel.rut
                ).filter(
                    BranchOfficeModel.principal_supervisor == rut
                ).filter(
                    *filters
                ).order_by(
                    DteModel.added_date.desc()
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
                    "id": dte.id,
                    "rut": dte.rut,
                    "branch_office_id": dte.branch_office_id,
                    "dte_type_id": dte.dte_type_id,
                    "customer": dte.customer,
                    "chip_id": dte.chip_id,
                    "folio": dte.folio,
                    "total": dte.total,
                    "payment_date": dte.payment_date,
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
                    "chip_id": dte.chip_id,
                    "folio": dte.folio,
                    "total": dte.total,
                    "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                    "payment_date": dte.payment_date,
                    "branch_office": dte.branch_office,
                    "status_id": dte.status_id
                } for dte in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}

    def search(self, branch_office_id=None, rut=None, status_id=None, supervisor_id=None, page=0, items_per_page=10):
        try:
            # Inicialización de filtros dinámicos
            filters = []

            if branch_office_id != None and branch_office_id != "":
                filters.append(DteModel.branch_office_id == branch_office_id)
            if rut != None and rut != "":
                filters.append(DteModel.rut == rut)
            if status_id != None and status_id != "":
                filters.append(DteModel.status_id == status_id)
            if supervisor_id != None and supervisor_id != "":
                filters.append(UserModel.supervisor_id == supervisor_id)

            filters.append(DteModel.dte_version_id == 1)
            filters.append(DteModel.status_id > 3)
            filters.append(DteModel.rut != None)
            filters.append(DteModel.rut != '66666666-6')
            
            if supervisor_id != None:
                # Construir la consulta base con los filtros aplicados
                query = self.db.query(
                    DteModel.id, 
                    DteModel.branch_office_id, 
                    DteModel.folio, 
                    DteModel.total,
                    DteModel.added_date,
                    DteModel.rut,
                    DteModel.status_id,
                    DteModel.chip_id,
                    DteModel.payment_date,
                    CustomerModel.customer,
                    BranchOfficeModel.branch_office
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
                ).outerjoin(
                    UserModel, UserModel.rut == BranchOfficeModel.principal_supervisor
                ).outerjoin(
                    CustomerModel, CustomerModel.rut == DteModel.rut
                ).filter(
                    *filters
                ).order_by(
                    desc(DteModel.folio)
                )
            else:
                # Construir la consulta base con los filtros aplicados
                query = self.db.query(
                    DteModel.id, 
                    DteModel.branch_office_id, 
                    DteModel.folio, 
                    DteModel.total,
                    DteModel.added_date,
                    DteModel.rut,
                    DteModel.status_id,
                    DteModel.payment_date,
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
                    desc(DteModel.folio)
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
                    "payment_date": dte.payment_date,
                    "customer": dte.customer,
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
                    "payment_date": dte.payment_date,
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
    
    def get_all_to_review(self, rol_id = None, rut = None, page=1, items_per_page=10):
        try:
            if rol_id == 1 or rol_id == 2:
                # Inicialización de filtros dinámicos
                filters = []

                filters.append(DteModel.dte_version_id == 1)
                filters.append(DteModel.status_id == 16)
                filters.append(DteModel.rut != None)
                filters.append(DteModel.rut != '66666666-6')
                filters.append(or_(DteModel.dte_type_id == 33, DteModel.dte_type_id == 39))

                # Construir la consulta base con los filtros aplicados
                query = self.db.query(
                        DteModel.id, 
                        DteModel.branch_office_id, 
                        DteModel.dte_type_id, 
                        DteModel.folio, 
                        DteModel.total,
                        DteModel.added_date,
                        DteModel.rut,
                        DteModel.status_id,
                        DteModel.chip_id,
                        DteModel.payment_date,
                        BranchOfficeModel.branch_office,
                        CustomerModel.customer.label('customer')
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
                ).outerjoin(
                    CustomerModel, CustomerModel.rut == DteModel.rut
                ).filter(
                    *filters
                ).order_by(
                    DteModel.added_date.desc()
                )
            elif rol_id == 4:
                                # Inicialización de filtros dinámicos
                filters = []

                filters.append(DteModel.dte_version_id == 1)
                filters.append(DteModel.status_id == 16)
                filters.append(DteModel.rut != None)
                filters.append(DteModel.rut != '66666666-6')
                filters.append(or_(DteModel.dte_type_id == 33, DteModel.dte_type_id == 39))

                # Construir la consulta base con los filtros aplicados
                query = self.db.query(
                        DteModel.id, 
                        DteModel.branch_office_id, 
                        DteModel.dte_type_id, 
                        DteModel.folio, 
                        DteModel.total,
                        DteModel.added_date,
                        DteModel.rut,
                        DteModel.status_id,
                        DteModel.payment_date,
                        DteModel.chip_id,
                        BranchOfficeModel.branch_office,
                        CustomerModel.customer.label('customer')
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
                ).outerjoin(
                    CustomerModel, CustomerModel.rut == DteModel.rut
                ).filter(
                    BranchOfficeModel.principal_supervisor == rut
                ).filter(
                    *filters
                ).order_by(
                    DteModel.added_date.desc()
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
                    "id": dte.id,
                    "rut": dte.rut,
                    "branch_office_id": dte.branch_office_id,
                    "dte_type_id": dte.dte_type_id,
                    "customer": dte.customer,
                    "chip_id": dte.chip_id,
                    "folio": dte.folio,
                    "total": dte.total,
                    "payment_date": dte.payment_date,
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
                    "chip_id": dte.chip_id,
                    "folio": dte.folio,
                    "total": dte.total,
                    "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                    "payment_date": dte.payment_date,
                    "branch_office": dte.branch_office,
                    "status_id": dte.status_id
                } for dte in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
    
    def update(self, form_data):
        """
        Actualiza los datos de la patente en la base de datos.
        """
        dte = self.db.query(DteModel).filter(DteModel.id == form_data.id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        # Actualizar campos
        dte.branch_office_id = form_data.branch_office_id
        dte.rut = form_data.rut
        dte.cash_amount = form_data.amount + 5000 if form_data.chip_id == 1 else form_data.amount
        dte.subtotal = round((form_data.amount + 5000)/1.19) if form_data.chip_id == 1 else round((form_data.amount)/1.19)
        dte.tax = (form_data.amount + 5000) - round((form_data.amount + 5000)/1.19) if form_data.chip_id == 1 else form_data.amount - round((form_data.amount)/1.19)
        dte.discount = 0
        dte.total = form_data.amount + 5000 if form_data.chip_id == 1 else form_data.amount
        dte.chip_id = form_data.chip_id
        dte.status_id = 2

        self.db.commit()
        self.db.refresh(dte)
    
    def accept_dte_payment(self, id):
        """
        Actualiza los datos de la patente en la base de datos.
        """
        dte = self.db.query(DteModel).filter(DteModel.id == id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        # Actualizar campos
        dte.status_id = 5

        self.db.commit()
        self.db.refresh(dte)

    def reject_dte_payment(self, id):
        """
        Actualiza los datos de la patente en la base de datos.
        """
        dte = self.db.query(DteModel).filter(DteModel.id == id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        # Actualizar campos
        dte.payment_type_id = None
        dte.payment_date = None
        dte.payment_amount = None
        dte.payment_number = None
        dte.support = None
        dte.status_id = 4

        self.db.commit()
        self.db.refresh(dte)

    def change_status(self, form_data):
        """
        Actualiza los datos de la patente en la base de datos.
        """
        dte = self.db.query(DteModel).filter(DteModel.id == form_data.id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        # Actualizar campos
        dte.expense_type_id = form_data.expense_type_id
        dte.payment_type_id = form_data.payment_type_id
        dte.payment_date = form_data.payment_date
        period = form_data.payment_date.split('-')
        dte.period = period[0] + '-' + period[1]
        dte.comment = form_data.comment
        dte.status_id = 5

        self.db.commit()
        self.db.refresh(dte)

        self.create_account_asset(dte)

    def reject(self, id):
        dte = self.db.query(DteModel).filter(DteModel.id == id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        dte.status_id = 3

        self.db.commit()
        self.db.refresh(dte)

    def get(self, id):
        try:
            data_query = self.db.query(DteModel.id, DteModel.payment_type_id, DteModel.payment_date, DteModel.payment_amount, DteModel.payment_number, DteModel.support, DteModel.period, DteModel.rut, DteModel.branch_office_id, DteModel.total, CustomerModel.address, DteModel.cash_amount, CustomerModel.customer, CustomerModel.region_id, CustomerModel.commune_id, CustomerModel.activity, CustomerModel.email, CustomerModel.phone, DteModel.chip_id, DteModel.folio, DteModel.status_id, DteModel.added_date, BranchOfficeModel.branch_office). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id). \
                        outerjoin(CustomerModel, CustomerModel.rut == DteModel.rut). \
                        filter(DteModel.id == id). \
                        first()

            if data_query:
                # Serializar los datos del empleado
                customer_ticket_data = {
                    "id": data_query.id,
                    "rut": data_query.rut,
                    "branch_office_id": data_query.branch_office_id,
                    "customer": data_query.customer,
                    "email": data_query.email,
                    "phone": data_query.phone,
                    "chip_id": data_query.chip_id,
                    "folio": data_query.folio,
                    "activity": data_query.activity,
                    "region_id": data_query.region_id,
                    "commune_id": data_query.commune_id,
                    "address": data_query.address,
                    "total": data_query.total,
                    "status_id": data_query.status_id,
                    "period": data_query.period,
                    "added_date": data_query.added_date.strftime('%d-%m-%Y') if data_query.added_date else None,
                    "branch_office": data_query.branch_office,
                    "payment_type_id": data_query.payment_type_id,
                    "payment_date": data_query.payment_date,
                    "payment_amount": data_query.payment_amount,
                    "payment_number": data_query.payment_number,
                    "support": data_query.support
                }

                # Crear el resultado final como un diccionario
                result = {
                    "customer_ticket_bill_data": customer_ticket_data
                }

                # Convierte el resultado a una cadena JSON
                serialized_result = json.dumps(result)

                return serialized_result

            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
            
    def create_account_asset(self, form_data):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        american_date = form_data.period + '-01'
        utf8_date = HelperClass.convert_to_utf8(american_date)
        expense_type = '441000102'
        branch_office = self.db.query(BranchOfficeModel).filter(
            BranchOfficeModel.id == form_data.branch_office_id
        ).first()

        gloss = (
                branch_office.branch_office
                + "_"
                + expense_type
                + "_"
                + utf8_date
                + "_NotaCredito_"
                + str(form_data.id)
                + "_"
                + str(form_data.folio)
            )
        amount = form_data.total
        
        data = {
                "fecha": american_date,
                "glosa": gloss,
                "detalle": {
                    "debe": {
                        expense_type: round(int(amount)/1.19),
                        "221000226": round(int(amount) - (int(amount)/1.19)),
                    },
                    "haber": {
                        "111000102": int(amount),
                    }
                },
                "operacion": "I",
                "documentos": {
                    "emitidos": [
                        {
                            "dte": form_data.dte_type_id,
                            "folio": form_data.folio,
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

        if response.status_code == 200:
            return "Accounting entry created successfully"
        else:
            return f"Accounting entry creation failed."

    def store_credit_note(self, form_data):
        dte = self.db.query(DteModel).filter(DteModel.id == form_data.id).first()
        
        customer = CustomerClass(self.db).get_by_rut(dte.rut)
        customer_data = json.loads(customer)

        dte_date = self.get_dte_date(dte.dte_type_id, dte.folio)

        code = self.pre_generate_credit_note_ticket(customer_data, dte.dte_type_id, dte.folio, dte.cash_amount, dte_date)

        print(code)

        folio = None

        if code is not None:
            if code == 402:
                return "LibreDTE payment required"

            folio = self.generate_credit_note_ticket(customer_data['customer_data']['rut'], code, dte.dte_type_id)

        if folio != None:
            dte.status_id = 5
            dte.reason_id = form_data.reason_id
            dte.comment = 'Código de autorización: Nota de Crédito ' + str(code)
            self.db.add(dte)
            self.db.commit()

            added_date = dte_date
            period = added_date.split(' ')
            period = period[0].split('-')
            period = period[0] + '-' + period[1]

            credit_note_dte = DteModel()
                    
            # Asignar los valores del formulario a la instancia del modelo
            credit_note_dte.branch_office_id = dte.branch_office_id
            credit_note_dte.cashier_id = 0
            credit_note_dte.dte_type_id = 61
            credit_note_dte.dte_version_id = 1
            credit_note_dte.status_id = 5
            credit_note_dte.chip_id = 0
            credit_note_dte.rut = customer_data['customer_data']['rut']
            credit_note_dte.folio = folio
            credit_note_dte.cash_amount = -abs(int(dte.cash_amount))
            credit_note_dte.card_amount = 0
            credit_note_dte.subtotal = -abs(round(int(dte.cash_amount)/1.19))
            credit_note_dte.tax = -abs(int(dte.cash_amount) - round(int(dte.cash_amount)/1.19))
            credit_note_dte.discount = 0
            credit_note_dte.total = -abs(int(dte.cash_amount))
            credit_note_dte.period = period
            credit_note_dte.added_date = dte.added_date

            self.db.add(credit_note_dte)
            self.db.commit()
            self.create_account_asset(credit_note_dte)

            update_dte = self.db.query(DteModel).filter(DteModel.folio == dte.folio).first()
            update_dte.status_id = 5
            self.db.add(update_dte)
            self.db.commit()
        else:
            return "Creditnote was not created"
    
    def get_dte_date(self, dte_type_id, folio):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        # Endpoint para generar un DTE temporal
        url = f"https://libredte.cl/api/dte/dte_emitidos/info/"+ str(dte_type_id) +"/" + str(folio) + '/76063822?getXML=0&getDetalle=0&getDatosDte=0&getTed=0&getResolucion=0&getEmailEnviados=0&getLinks=0&getReceptor=0&getSucursal=0&getUsuario=0'
            
        # Enviar solicitud a la API
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
            },
        )

        response_data = response.json()

        return response_data['fecha']

    def pre_generate_credit_note_ticket(self, customer_data, dte_type_id, folio, cash_amount, added_date):  # Added self as the first argument
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        amount = round(int(cash_amount)/1.19)

        data = {
                "Encabezado": {
                    "IdDoc": {
                        "TipoDTE": 61,
                        "FchEmis": added_date,
                        "TpoTranVenta": 1,
                        "FmaPago": "1",
                    },
                    "Emisor": {
                        "RUTEmisor": "76063822-6"
                    },
                    "Receptor": {
                        "RUTRecep": customer_data['customer_data']['rut'],
                        "RznSocRecep": customer_data['customer_data']['customer'],
                        "GiroRecep": customer_data['customer_data']['activity'],
                        "DirRecep": customer_data['customer_data']['region'],
                        "CmnaRecep": customer_data['customer_data']['commune'],
                    }
                },
                "Detalle": [
                    {
                        "NmbItem": "Nota de Crédito de Venta",
                        "QtyItem": 1,
                        "PrcItem": amount,
                        "MontoItem": amount,
                    }
                ],
                "Referencia": [ {
                    "TpoDocRef": dte_type_id,
                    "FolioRef": folio,
                    "FchRef": added_date,
                    "CodRef": 1,
                    "RazonRef": "Anula factura o boleta"
                }],
            }
        
        print(data)

        try:
            # Endpoint para generar un DTE temporal
            url = f"https://libredte.cl/api/dte/documentos/emitir?normalizar=1&formato=json&links=0&email=0"
            
            # Enviar solicitud a la API
            response = requests.post(
                url,
                json=data,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )
            
            # Manejar la respuesta
            if response.status_code == 200:
                dte_data = response.json()
                code = dte_data.get("codigo")

                return code
            else:
                return response.status_code

        except Exception as e:
            print("Error al conectarse a la API:", e)
            return None

    def generate_credit_note_ticket(self, customer_rut, code, dte_type_id):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        data = {
            "emisor": "76063822-6",
            "receptor": customer_rut,
            "dte": 61,
            "codigo": code
        }

        try:
            # Endpoint para generar un DTE temporal
            url = f"https://libredte.cl/api/dte/documentos/generar?getXML=0&links=0&email=1&retry=1&gzip=0"
            
            # Enviar solicitud a la API
            response = requests.post(
                url,
                json=data,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 200:
                dte_data = response.json()
                folio = dte_data.get("folio")

                return folio
            else:
                print("Error al generar el DTE:")
                print(response.status_code, response.json())
                return None

        except Exception as e:
            print("Error al conectarse a la API:", e)
            return None
        
    def download(self, id):
        dte = self.db.query(DteModel).filter(DteModel.id == id).first()

        if dte:
            TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

            # Endpoint para generar un DTE temporal
            url = f"https://libredte.cl/api/dte/dte_emitidos/pdf/39/"+ str(dte.folio) +"/76063822-6?formato=general&papelContinuo=0&copias_tributarias=1&copias_cedibles=1&cedible=0&compress=0&base64=0"

            # Enviar solicitud a la API
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )

            # Manejar la respuesta
            if response.status_code == 200:
                pdf_content = response.content
                timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                unique_id = uuid.uuid4().hex[:8]  # 8 caracteres únicos
                unique_filename = f"{timestamp}_{unique_id}.pdf"

                # Ruta remota en Azure
                remote_path = f"{unique_filename}"  # Organizar archivos en una carpeta específica

                self.file_class.temporal_upload(pdf_content, remote_path)  # Llamada correcta

                # Descargar archivo desde Azure File Share
                file_contents = self.file_class.download(remote_path)

                # Convertir el contenido del archivo a base64
                encoded_file = base64.b64encode(file_contents).decode('utf-8')

                self.file_class.delete(remote_path)  # Llamada correcta

                # Retornar el nombre del archivo y su contenido como base64
                return {
                    "file_name": unique_filename,
                    "file_data": encoded_file
                }
            else:
                return None
            
    def verify(self, id):
        """
        Actualiza los datos de la patente en la base de datos.
        """
        dte = self.db.query(DteModel).filter(DteModel.id == id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        # Actualizar campos
        dte.status_id = 2
        self.db.commit()
        self.db.refresh(dte)