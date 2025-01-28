from sqlalchemy.orm import Session
from app.backend.db.models import DteModel, BranchOfficeModel
from app.backend.classes.file_class import FileClass
import requests
from datetime import datetime
from sqlalchemy import desc
from sqlalchemy.dialects import mysql
import uuid
import base64
from sqlalchemy import or_
import json

class MachineTicketClass:
    def __init__(self, db: Session):
        self.db = db
        self.file_class = FileClass(db)  # Crear una instancia de FileClass

    def get_all(self, page=0, items_per_page=10):
        try:
            # Inicialización de filtros dinámicos
            filters = []

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
                BranchOfficeModel.branch_office
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
            ).filter(
                *filters
            ).order_by(
                desc(DteModel.id)
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
                    "entrance_hour": dte.entrance_hour,
                    "exit_hour": dte.exit_hour,
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
                    "entrance_hour": dte.entrance_hour,
                    "exit_hour": dte.exit_hour,
                    "folio": dte.folio,
                    "total": dte.total,
                    "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                    "branch_office": dte.branch_office,
                    "status_id": dte.status_id
                } for dte in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}

    def search(self, branch_office_id=None, dte_type_id=None, amount=None, since=None, until=None, page=0, items_per_page=10):
        try:
            # Inicialización de filtros dinámicos
            filters = []

            if branch_office_id is not None:
                filters.append(DteModel.branch_office_id == branch_office_id)
            if amount is not None:
                filters.append(DteModel.total == amount)
            if dte_type_id is not None:
                filters.append(DteModel.dte_type_id == dte_type_id)
            if until is not None:
                filters.append(DteModel.added_date <= until)  # Fecha desde
            if since is not None:
                filters.append(DteModel.added_date >= since)  # Fecha hasta

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
                BranchOfficeModel.branch_office
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
            ).filter(
                *filters
            ).order_by(
                desc(DteModel.id)
            )

            print(query)
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
                    "entrance_hour": dte.entrance_hour,
                    "exit_hour": dte.exit_hour,
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
                    "entrance_hour": dte.entrance_hour,
                    "exit_hour": dte.exit_hour,
                    "folio": dte.folio,
                    "total": dte.total,
                    "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                    "branch_office": dte.branch_office,
                    "status_id": dte.status_id
                } for dte in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
        
    def download(self, id):
        dte = self.db.query(DteModel).filter(DteModel.id == id).first()

        if dte:
            payload = {
                "credenciales": {
                    "rutEmisor": "76063822-6",
                    "nombreSucursal": "Casa Matriz",
                },
                "dteReferenciadoExterno": {
                    "folio": dte.folio,
                    "codigoTipoDte": dte.dte_type_id,
                    "ambiente": 1
                }
            }

            url = f"https://api.simplefactura.cl/getPdf"

            headers = {
                'Authorization': 'Basic cm9kcmlnb2NhYmV6YXNAamlzcGFya2luZy5jb206Um9ybzIwMjQu',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                url,
                json=payload,
                headers=headers,
            )

            if response.status_code == 200:
                pdf_content = response.content
                timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                unique_id = uuid.uuid4().hex[:8]
                unique_filename = f"{timestamp}_{unique_id}.pdf"

                remote_path = f"{unique_filename}"

                self.file_class.temporal_upload(pdf_content, remote_path)

                file_contents = self.file_class.download(remote_path)

                print(file_contents)

                encoded_file = base64.b64encode(file_contents).decode('utf-8')

                self.file_class.delete(remote_path)

                return {
                    "file_name": unique_filename,
                    "file_data": encoded_file
                }
            else:
                return None
            
    def get_dte_date(self, folio):
        payload = {
                "credenciales": {
                    "rutEmisor": "76063822-6",
                    "nombreSucursal": "Casa Matriz",
                },
                "dteReferenciadoExterno": {
                    "folio": folio,
                    "codigoTipoDte": 39,
                    "ambiente": 1
                }
            }

        url = f"https://api.simplefactura.cl/documentIssued"
        
        headers = {
                'Authorization': 'Basic cm9kcmlnb2NhYmV6YXNAamlzcGFya2luZy5jb206Um9ybzIwMjQu',
                'Content-Type': 'application/json'
            }
        
        response = requests.post(
                url,
                json=payload,
                headers=headers,
            )

        response_data = response.json()

        return response_data['data']['fechaDte']
            
    def store_credit_note(self, form_data):
        dte = self.db.query(DteModel).filter(DteModel.id == form_data.id).first()
        
        dte_date = self.get_dte_date(dte.folio)

        folio = self.generate_credit_note_ticket(dte.folio, dte.cash_amount, dte_date)

        if folio != None:
            dte.status_id = 5
            dte.reason_id = form_data.reason_id
            dte.comment = 'Folio de la Nota de Crédito ' + str(folio)
            self.db.add(dte)
            self.db.commit()

            credit_note_dte = DteModel()
                    
            credit_note_dte.branch_office_id = dte.branch_office_id
            credit_note_dte.cashier_id = 0
            credit_note_dte.dte_type_id = 61
            credit_note_dte.dte_version_id = 1
            credit_note_dte.status_id = 5
            credit_note_dte.chip_id = 0
            credit_note_dte.rut = '66666666-6'
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

                self.create_account_asset(credit_note_dte)

                return {"status": "success", "message": "Credit Note saved successfully"}
            except Exception as e:
                self.db.rollback()
                return {"status": "error", "message": f"Error: {str(e)}"}
        else:
            return "Creditnote was not created"
        
    def generate_credit_note_ticket(self, folio, cash_amount, added_date):
        added_date = added_date.split("-")
        added_date = f"{added_date[2]}-{added_date[1]}-{added_date[0]}"

        data = {
                "Documento": {
                    "Encabezado": {
                        "IdDoc": {
                            "TipoDTE": 61,
                            "FchEmis": added_date
                        },
                        "Emisor": {
                            "RUTEmisor": "76063822-6",
                            "RznSoc": "Jisparking SpA",
                            "DirOrigen": "Matucana 40",
                            "CmnaOrigen": "Santiago"
                        },
                        "Receptor": {
                            "RUTRecep":"66666666-6",
                            "RznSocRecep": "Cliente en Sucursal"
                        },
                        "Totales": {
                            "MntTotal": cash_amount
                        }
                    },
                    "Detalle": [{
                        "NroLinDet": "1",
                        "IndExe": 0,
                        "NmbItem": "Venta",
                        "QtyItem": "1",
                        "PrcItem": cash_amount,
                        "MontoItem": cash_amount
                    }],
                    "Referencia":[{
                        "NroLinRef":1,
                        "TpoDocRef":"39",
                        "FolioRef":str(folio),
                        "FchRef":added_date,
                        "CodRef":1,
                        "RazonRef":"Nota de Crédito para Caja Automática"
                    }]
                }
            }
        
        print(data)

        url = f"https://api.simplefactura.cl/invoiceCreditDebitNotesV2/Casa_Matriz/6"

        headers = {
                'Authorization': 'Basic cm9kcmlnb2NhYmV6YXNAamlzcGFya2luZy5jb206Um9ybzIwMjQu',
                'Content-Type': 'application/json'
            }
        
        response = requests.post(
                url,
                json=data,
                headers=headers,
            )
        
        data = json.loads(response.text)

        # Extraer el folio
        folio = data["data"]["folio"]

        return folio


