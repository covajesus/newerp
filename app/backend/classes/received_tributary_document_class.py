from sqlalchemy.orm import Session
from app.backend.db.models import DteModel, CustomerModel, BranchOfficeModel, UserModel, SupplierModel, ExpenseTypeModel
from app.backend.classes.customer_class import CustomerClass
from app.backend.classes.file_class import FileClass
from sqlalchemy import desc
from sqlalchemy.dialects import mysql
from sqlalchemy import or_
from fastapi import HTTPException
import requests
import json
import base64
import uuid
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from app.backend.classes.helper_class import HelperClass

class ReceivedTributaryDocumentClass:
    def __init__(self, db: Session):
        self.db = db
        self.file_class = FileClass(db)  # Crear una instancia de FileClass

    def get_all(self, page=0, items_per_page=10):
        try:
            # Inicialización de filtros dinámicos
            filters = []

            filters.append(DteModel.dte_version_id == 2)
            filters.append(DteModel.dte_type_id == 33)
            filters.append(DteModel.rut != None)

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
                SupplierModel.supplier,
                BranchOfficeModel.branch_office
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
            ).outerjoin(
                SupplierModel, SupplierModel.rut == DteModel.rut
            ).filter(
                *filters
            ).order_by(
                DteModel.id.desc()
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
                    "supplier": dte.supplier,
                    "chip_id": dte.chip_id,
                    "folio": dte.folio,
                    "total": dte.total,
                    "status_id": dte.status_id,
                    "added_date": dte.added_date.strftime('%Y-%m-%d') if dte.added_date else None,
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
                    "supplier": dte.supplier,
                    "chip_id": dte.chip_id,
                    "folio": dte.folio,
                    "total": dte.total,
                    "added_date": dte.added_date.strftime('%Y-%m-%d') if dte.added_date else None,
                    "branch_office": dte.branch_office,
                    "status_id": dte.status_id
                } for dte in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}

    def get_all_supplier_bills(self, rut):
        try:
            # Inicialización de filtros dinámicos
            filters = []

            filters.append(DteModel.dte_version_id == 2)
            filters.append(DteModel.dte_type_id == 33)
            filters.append(DteModel.rut == rut)
            filters.append(DteModel.status_id == 4)

            # Construir la consulta base con los filtros aplicados
            query = self.db.query(
                DteModel.id, 
                DteModel.branch_office_id, 
                DteModel.folio, 
                DteModel.total,
                DteModel.added_date,
                DteModel.rut,
                ExpenseTypeModel.expense_type,
                DteModel.status_id,
                DteModel.chip_id,
                SupplierModel.supplier,
                BranchOfficeModel.branch_office
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
            ).outerjoin(
                SupplierModel, SupplierModel.rut == DteModel.rut
            ).outerjoin(
                ExpenseTypeModel, ExpenseTypeModel.id == DteModel.expense_type_id
            ).filter(
                *filters
            ).order_by(
                DteModel.id.desc()
            )

            data = query.all()

            # Serializar los datos
            serialized_data = [{
                    "id": dte.id,
                    "rut": dte.rut,
                    "branch_office_id": dte.branch_office_id,
                    "expense_type": dte.expense_type,
                    "supplier": dte.supplier,
                    "chip_id": dte.chip_id,
                    "folio": dte.folio,
                    "total": dte.total,
                    "added_date": dte.added_date.strftime('%Y-%m-%d') if dte.added_date else None,
                    "branch_office": dte.branch_office,
                    "status_id": dte.status_id
            } for dte in data]

            return {
                    "data": serialized_data
                }

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
        
    def getTotalPerSupplier(self):
        try:
            # Inicialización de filtros dinámicos
            filters = []

            filters.append(DteModel.dte_version_id == 2)
            filters.append(DteModel.dte_type_id == 33)
            filters.append(DteModel.rut != None)
            filters.append(DteModel.status_id == 4)

            query = self.db.query(
                SupplierModel.rut,
                SupplierModel.supplier,
                func.sum(DteModel.total).label('total')
            ).outerjoin(
                SupplierModel, SupplierModel.rut == DteModel.rut
            ).filter(
                *filters
            ).group_by(
                SupplierModel.supplier,
                SupplierModel.rut
            ).order_by(
                SupplierModel.supplier
            )

            data = query.all()

            serialized_data = [{
                    "rut": dte.rut,
                    "supplier": dte.supplier,
                    "total": dte.total
                } for dte in data]

            return {
                "data": serialized_data
            }
        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
    
    def refresh(self):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
        since = (datetime.now() - timedelta(days=89)).strftime('%Y-%m-%d')
        until = datetime.now().strftime('%Y-%m-%d')
        
        data = {
            "fecha_desde": since,
            "fecha_hasta": until
        }

        try:
            url = "https://libredte.cl/api/dte/dte_recibidos/buscar/76063822?fecha_desde="+ str(since) +"&fecha_hasta=" + str(until)

            response = requests.get(
                url,
                json=data,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )
            
            data = json.loads(response.text)


            for item in data:
                # 👉 Validar que el emisor exista
                if not item.get('emisor'):
                    return 1
                else:
                    if item['emisor'] < 10000000:
                        item['emisor'] = '0' + str(item['emisor'])

                    verificator_digit = HelperClass.verificator_digit(item['emisor'])
                    rut = str(item['emisor']) + '-' + str(verificator_digit)

                    total = item['total'] if item['total'] is not None else 0
                    net = item['neto'] if item['total'] is not None else 0

                    validate_supplier_existence = self.db.query(SupplierModel).filter(SupplierModel.rut == rut).count()
                    if validate_supplier_existence == 0:
                        supplier = SupplierModel()
                        supplier.rut = rut
                        supplier.supplier = item['razon_social'].upper()
                        self.db.add(supplier)
                        self.db.commit()

                    dte_validation = self.db.query(DteModel).filter(
                        DteModel.folio == item['folio'],
                        DteModel.rut == rut,
                        DteModel.dte_type_id == item['dte'],
                        DteModel.dte_version_id == 2
                    ).count()
                    print(item['folio'])
                    if dte_validation == 0:
                        dte = DteModel()
                        dte.branch_office_id = 0
                        dte.cashier_id = 0
                        dte.dte_type_id = item['dte']
                        dte.dte_version_id = 2
                        dte.status_id = 1
                        dte.chip_id = 0
                        dte.rut = rut
                        dte.folio = item['folio']
                        dte.cash_amount = total
                        dte.card_amount = 0
                        dte.subtotal = net
                        dte.tax = int(total) - int(net)
                        dte.discount = 0
                        dte.total = total
                        dte.added_date = str(item['fecha']) + ' 00:00:00'

                        print(item['fecha'])

                        self.db.add(dte)
                        self.db.commit()

        except Exception as e:
            print("Error al conectarse a la API:", e)
            return None

    
    def pay(self, form_data):
        selected_bills = form_data.selected_bills

        for bill in selected_bills:
            dte = self.db.query(DteModel).filter(DteModel.id == bill.id).first()
            if not dte:
                raise HTTPException(status_code=404, detail="Dte no encontrado")

            dte.payment_date = form_data.payment_date
            dte.payment_type_id = form_data.payment_type_id
            dte.status_id = 5
            dte.payment_comment = form_data.comment

            self.db.commit()
            self.db.refresh(dte)

    def update(self, form_data):
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
    
    def change_status(self, form_data):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        dte = self.db.query(DteModel).filter(DteModel.id == form_data.id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        dte.branch_office_id = form_data.branch_office_id
        dte.expense_type_id = form_data.expense_type_id
        dte.period = form_data.period
        dte.status_id = form_data.status_id
        dte.comment = form_data.comment

        self.db.commit()
        self.db.refresh(dte)

        # Validar que los cambios se reflejan correctamente
        if (
            dte.branch_office_id == form_data.branch_office_id
            and dte.expense_type_id == form_data.expense_type_id
            and dte.period == form_data.period
            and dte.status_id == form_data.status_id
        ):
            print("Datos actualizados correctamente en la base de datos")
        else:
            raise ValueError("Error: Los datos no se actualizaron correctamente")

        american_date = form_data.period + '-01'
        utf8_date = HelperClass.convert_to_utf8(american_date)
        expense_type = self.db.query(ExpenseTypeModel).filter(
            ExpenseTypeModel.id == form_data.expense_type_id
        ).first()
        branch_office = self.db.query(BranchOfficeModel).filter(
            BranchOfficeModel.id == form_data.branch_office_id
        ).first()

        gloss = (
            branch_office.branch_office
            + "_"
            + expense_type.accounting_account
            + "_"
            + utf8_date
            + "_FacturaCompra_"
            + str(dte.id)
            + "_"
            + str(dte.folio)
        )
        amount = dte.total
       
        data = {
            "fecha": american_date,
            "glosa": gloss,
            "detalle": {
                "debe": {
                    expense_type.accounting_account.strip(): round(amount / 1.19),
                    "111000122": round(amount - (amount / 1.19)),
                },
                "haber": {
                    "111000102": amount,
                },
            },
            "operacion": "E",
            "documentos": {
                "recibidos": [
                    {
                        "dte": dte.dte_type_id,
                        "folio": dte.folio,
                    }
                ]
            },
        }

        try:
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

        except Exception as e:
            print("Error al conectarse a la API:", e)
            return None

    def reject(self, id):
        dte = self.db.query(DteModel).filter(DteModel.id == id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        dte.status_id = 3

        self.db.commit()
        self.db.refresh(dte)

    def get(self, id):
        try:
            data_query = self.db.query(DteModel.id, DteModel.rut, DteModel.branch_office_id, DteModel.total, DteModel.cash_amount, SupplierModel.supplier, DteModel.folio, DteModel.status_id, DteModel.added_date, BranchOfficeModel.branch_office). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id). \
                        outerjoin(SupplierModel, SupplierModel.rut == DteModel.rut). \
                        filter(DteModel.id == id). \
                        first()

            if data_query:
                # Serializar los datos del empleado
                received_tributary_document = {
                    "id": data_query.id,
                    "rut": data_query.rut,
                    "branch_office_id": data_query.branch_office_id,
                    "supplier": data_query.supplier,
                    "folio": data_query.folio,
                    "total": data_query.total,
                    "status_id": data_query.status_id,
                    "added_date": data_query.added_date.strftime('%d-%m-%Y') if data_query.added_date else None,
                    "branch_office": data_query.branch_office
                }

                result = {
                    "received_tributary_document_data": received_tributary_document
                }

                serialized_result = json.dumps(result)

                return serialized_result

            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store_credit_note(self, form_data):
        dte = self.db.query(DteModel).filter(DteModel.id == form_data.id).first()
        
        customer = CustomerClass(self.db).get_by_rut(dte.rut)
        customer_data = json.loads(customer)

        dte_date = self.get_dte_date(dte.folio)

        code = self.pre_generate_credit_note_ticket(customer_data, dte.folio, dte.cash_amount, dte_date)

        folio = None

        if code is not None:
            if code == 402:
                return "LibreDTE payment required"

            folio = self.generate_credit_note_ticket(customer_data['customer_data']['rut'], code)

        if folio != None:
            dte.status_id = 5
            dte.reason_id = form_data.reason_id
            dte.comment = 'Código de autorización: Nota de Crédito ' + str(code)
            self.db.add(dte)
            self.db.commit()

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
            credit_note_dte.cash_amount = dte.cash_amount
            credit_note_dte.card_amount = 0
            credit_note_dte.subtotal = round(dte.cash_amount/1.19)
            credit_note_dte.tax = (dte.cash_amount) - round((dte.cash_amount)/1.19)
            credit_note_dte.discount = 0
            credit_note_dte.total = dte.cash_amount
            credit_note_dte.added_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            self.db.add(credit_note_dte)
            
            try:
                self.db.commit()
                return {"status": "success", "message": "Credit Note saved successfully"}
            except Exception as e:
                self.db.rollback()
                return {"status": "error", "message": f"Error: {str(e)}"}
        else:
            return "Creditnote was not created"
        
    def pre_generate_ticket(self, customer_data, form_data):  # Added self as the first argument
        branch_office_data = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == form_data.branch_office_id).first()

        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        if form_data.chip_id == 1:
            if form_data.will_save == 0 or form_data.will_save == None or form_data.will_save == "":
                amount = form_data.amount - 5000
            else:
                amount = form_data.amount

            data = {
                "Encabezado": {
                    "IdDoc": {
                        "TipoDTE": 39
                    },
                    "Emisor": {
                        "RUTEmisor": "76063822-6",
                        'CdgSIISucur': branch_office_data.dte_code,
                    },
                    "Receptor": {
                        "RUTRecep": customer_data['customer_data']['rut'],
                        "RznSocRecep": customer_data['customer_data']['customer'],
                        "GiroRecep": customer_data['customer_data']['activity'],
                        "DirRecep": customer_data['customer_data']['region'],
                        "CmnaRecep": customer_data['customer_data']['commune'],
                        'Contacto': customer_data['customer_data']['email'],
                        'CorreoRecep': customer_data['customer_data']['email'],
                    }
                },
                "Detalle": [
                    {
                        "NmbItem": "Venta",
                        "QtyItem": 1,
                        "PrcItem": amount,
                    },
                    {
                        "NmbItem": "Chip",
                        "QtyItem": 1,
                        "PrcItem": 5000,
                    },
                ]
            }
        else:
            data = {
                "Encabezado": {
                    "IdDoc": {
                        "TipoDTE": 39
                    },
                    "Emisor": {
                        "RUTEmisor": "76063822-6",
                        'CdgSIISucur': branch_office_data.dte_code,
                    },
                    "Receptor": {
                        "RUTRecep": customer_data['customer_data']['rut'],
                        "RznSocRecep": customer_data['customer_data']['customer'],
                        "GiroRecep": customer_data['customer_data']['activity'],
                        "DirRecep": customer_data['customer_data']['region'],
                        "CmnaRecep": customer_data['customer_data']['commune'],
                        'Contacto': customer_data['customer_data']['email'],
                        'CorreoRecep': customer_data['customer_data']['email'],
                    }
                },
                "Detalle": [
                    {
                        "NmbItem": "Venta",
                        "QtyItem": 1,
                        "PrcItem": form_data.amount,
                    }
                ]
            }

        try:
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
            
            if response.status_code == 200:
                dte_data = response.json()
                print(dte_data)
                code = dte_data.get("codigo")

                return code
            else:
                return response.status_code

        except Exception as e:
            print("Error al conectarse a la API:", e)
            return None
    
    def get_dte_date(self, folio):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        url = f"https://libredte.cl/api/dte/dte_emitidos/info/39/" + str(folio) + '/76063822?getXML=0&getDetalle=0&getDatosDte=0&getTed=0&getResolucion=0&getEmailEnviados=0&getLinks=0&getReceptor=0&getSucursal=0&getUsuario=0'
            
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
            },
        )

        response_data = response.json()
        print(response_data)

        return response_data['fecha']

    def pre_generate_credit_note_ticket(self, customer_data, folio, cash_amount, added_date):  # Added self as the first argument
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        amount = round(cash_amount/1.19)

        data = {
                "Encabezado": {
                    "IdDoc": {
                        "TipoDTE": "61",
                        "Folio": 0,
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
                    "TpoDocRef": 39,
                    "FolioRef": folio,
                    "FchRef": added_date,
                    "CodRef": 1,
                    "RazonRef": "Anula factura o boleta"
                }],
            }

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
            
            print(response.text)
            # Manejar la respuesta
            if response.status_code == 200:
                dte_data = response.json()
                print(dte_data)
                code = dte_data.get("codigo")

                return code
            else:
                return response.status_code

        except Exception as e:
            print("Error al conectarse a la API:", e)
            return None
        
    def generate_ticket(self, customer_rut, code):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        data = {
            "emisor": "76063822-6",
            "receptor": customer_rut,
            "dte": 39,
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
            
            # Manejar la respuesta
            print(response)

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

    def generate_credit_note_ticket(self, customer_rut, code):
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
            
            # Manejar la respuesta
            print(response)

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

        issuer_rut = HelperClass().numeric_rut(dte.rut)

        if dte:
            TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

            url = f"https://libredte.cl/api/dte/dte_recibidos/pdf/"+ str(issuer_rut) +"/33/"+ str(dte.folio) +"/76063822?papelContinuo=0&copias_tributarias=1&copias_cedibles=0&cedible=0&compress=0&base64=0"

            response = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )

            print(response.content)

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