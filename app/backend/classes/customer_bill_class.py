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

class CustomerBillClass:
    def __init__(self, db: Session):
        self.db = db
        self.file_class = FileClass(db)  # Crear una instancia de FileClass

    def get_all(self, group = 1, page=0, items_per_page=10):
        try:
            # Inicialización de filtros dinámicos
            filters = []

            filters.append(DteModel.dte_version_id == 1)
            filters.append(DteModel.dte_type_id == 33)
            filters.append(DteModel.rut != None)

            if group == 1:
                filters.append(or_(DteModel.status_id == 1, DteModel.status_id == 2, DteModel.status_id == 3))
            else:
                filters.append(or_(DteModel.status_id == 4, DteModel.status_id == 5))

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
    
    def get(self, id):
        try:
            data_query = self.db.query(DteModel.id, DteModel.rut, DteModel.branch_office_id, DteModel.total, CustomerModel.customer, CustomerModel.email, CustomerModel.phone, DteModel.chip_id, DteModel.folio, DteModel.status_id, DteModel.added_date, BranchOfficeModel.branch_office). \
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
                    "total": data_query.total,
                    "status_id": data_query.status_id,
                    "added_date": data_query.added_date.strftime('%d-%m-%Y') if data_query.added_date else None,
                    "branch_office": data_query.branch_office
                }

                # Crear el resultado final como un diccionario
                result = {
                    "customer_ticket_data": customer_ticket_data
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
        customer = CustomerClass(self.db).get_by_rut(form_data.rut)
        customer_data = json.loads(customer)
        code = self.pre_generate_bill(customer_data, form_data)

        if code is not None:
            folio = self.generate_bill(customer_data['customer_data']['rut'], code)

        if form_data.will_save == 1:
            if folio != None:
                dte = DteModel()
                
                # Asignar los valores del formulario a la instancia del modelo
                dte.branch_office_id = form_data.branch_office_id
                dte.cashier_id = 0
                dte.dte_type_id = 33
                dte.dte_version_id = 1
                dte.status_id = 4
                dte.chip_id = form_data.chip_id
                dte.rut = form_data.rut
                dte.folio = folio
                dte.cash_amount = form_data.amount + 5000 if form_data.chip_id == 1 else form_data.amount
                dte.card_amount = 0
                dte.subtotal = round((form_data.amount + 5000)/1.19) if form_data.chip_id == 1 else round((form_data.amount)/1.19)
                dte.tax = (form_data.amount + 5000) - round((form_data.amount + 5000)/1.19) if form_data.chip_id == 1 else form_data.amount - round((form_data.amount)/1.19)
                dte.discount = 0
                dte.total = form_data.amount + 5000 if form_data.chip_id == 1 else form_data.amount
                dte.added_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

                self.db.add(dte)

                try:
                    self.db.commit()
                    return {"status": "success", "message": "Dte saved successfully"}
                except Exception as e:
                    self.db.rollback()
                    return {"status": "error", "message": f"Error: {str(e)}"}
            else:
                return 'error'
        else:
            if folio != None:
                dte = self.db.query(DteModel).filter(DteModel.id == form_data.id).first()
                dte.folio = folio
                dte.status_id = 4
                self.db.add(dte)

                try:
                    self.db.commit()
                    return {"status": "success", "message": "Dte saved successfully"}
                except Exception as e:
                    self.db.rollback()
                    return {"status": "error", "message": f"Error: {str(e)}"}
            else:
                return 'error'
    
    def pre_generate_bill(self, customer_data, form_data):  # Added self as the first argument
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        if form_data.chip_id == 1:
            data = {
                "Encabezado": {
                    "IdDoc": {
                        "TipoDTE": 33,
                        "MntBruto": 1
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
                        "NmbItem": "Venta",
                        "QtyItem": 1,
                        "PrcItem": form_data.amount,
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
                        "TipoDTE": 33,
                        "MntBruto": 1
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
                        "NmbItem": "Venta",
                        "QtyItem": 1,
                        "PrcItem": form_data.amount,
                    }
                ]
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
            
            # Manejar la respuesta
            if response.status_code == 200:
                dte_data = response.json()
                code = dte_data.get("codigo")

                return code
            else:
                return None

        except Exception as e:
            print("Error al conectarse a la API:", e)
            return None
        
    def generate_bill(self, customer_rut, code):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        data = {
            "emisor": "76063822-6",
            "receptor": customer_rut,
            "dte": 33,
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
            url = f"https://libredte.cl/api/dte/dte_emitidos/pdf/33/"+ str(dte.folio) +"/76063822-6?formato=general&papelContinuo=0&copias_tributarias=1&copias_cedibles=1&cedible=0&compress=0&base64=0"

            # Enviar solicitud a la API
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )

            
            print(response.status_code)
            
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