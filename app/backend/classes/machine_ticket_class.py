from sqlalchemy.orm import Session
from app.backend.db.models import DteModel, BranchOfficeModel, FolioModel
from app.backend.classes.helper_class import HelperClass
from app.backend.classes.file_class import FileClass
import requests
from datetime import datetime
from sqlalchemy import desc
from sqlalchemy.dialects import mysql
from app.backend.classes.setting_class import SettingClass
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
            filters.append(DteModel.rut == "66666666-6")

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
                DteModel.dte_type_id,
                DteModel.status_id,
                BranchOfficeModel.branch_office
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
            ).filter(
                *filters
            ).order_by(
                desc(DteModel.added_date)
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
                    "dte_type_id": dte.dte_type_id,
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
                    "dte_type_id": dte.dte_type_id,
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

    def search(self, folio=None, branch_office_id=None, dte_type_id=None, amount=None, since=None, until=None, page=0, items_per_page=10):
        try:
            # Inicialización de filtros dinámicos
            filters = []

            if folio is not None:
                filters.append(DteModel.folio == folio)
            if branch_office_id is not None:
                filters.append(DteModel.branch_office_id == branch_office_id)
            if amount is not None:
                filters.append(DteModel.total == amount)
            if until is not None:
                filters.append(DteModel.added_date <= until)  # Fecha desde
            if since is not None:
                filters.append(DteModel.added_date >= since)  # Fecha hasta
            if dte_type_id is not None:
                filters.append(DteModel.dte_type_id == dte_type_id)

            filters.append(DteModel.rut == '66666666-6')
            
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
                DteModel.dte_type_id,
                BranchOfficeModel.branch_office,
                FolioModel.requested_status_id,
                FolioModel.used_status_id,
                FolioModel.billed_status_id
            ).outerjoin(
                FolioModel, FolioModel.folio == DteModel.folio
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
            ).filter(
                *filters
            ).order_by(
                desc(DteModel.id)
            )

            check_credit_note_existence = self.db.query(DteModel).filter(
                DteModel.denied_folio == folio
            ).count()

            if check_credit_note_existence > 0:
                have_credit_note = 1
            else:
                have_credit_note = 0

        
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
                    "dte_type_id": dte.dte_type_id,
                    "folio": dte.folio,
                    "total": dte.total,
                    "status_id": dte.status_id,
                    "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                    "branch_office": dte.branch_office,
                    "requested_status_id": dte.requested_status_id,
                    "billed_status_id": dte.billed_status_id,
                    "used_status_id": dte.used_status_id,
                    "have_credit_note": have_credit_note
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
                    "dte_type_id": dte.dte_type_id,
                    "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                    "branch_office": dte.branch_office,
                    "status_id": dte.status_id,
                    "requested_status_id": dte.requested_status_id,
                    "used_status_id": dte.used_status_id,
                    "billed_status_id": dte.billed_status_id,
                    "have_credit_note": have_credit_note
                } for dte in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
        
    def download(self, id):
        setting_data = SettingClass(self.db).get()
        token = setting_data["setting_data"]["simplefactura_token"]
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
                'Authorization': f'Bearer {token}',
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
        setting_data = SettingClass(self.db).get()
        token = setting_data["setting_data"]["simplefactura_token"]

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
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        
        response = requests.post(
                url,
                json=payload,
                headers=headers,
            )
        
        print(response.text)

        response_data = response.json()

        return response_data['data']['fechaDte']
            
    def store_credit_note(self, form_data):
        dte = self.db.query(DteModel).filter(DteModel.id == form_data.id).first()
        
        dte_date = self.get_dte_date(dte.folio)
        dte_date_detail = dte_date.split("T")
        dte_date_detail = str(dte_date_detail[0]) + " 00:00:00"

        if int(dte.cash_amount) > 0:
            amount = dte.cash_amount
        else:
            amount = dte.card_amount

        folio = self.generate_credit_note_ticket(dte.folio, amount, dte_date)

        if folio != None:
            dte.status_id = 5
            dte.reason_id = form_data.reason_id
            dte.comment = 'Folio de la Nota de Crédito ' + str(folio)
            self.db.add(dte)
            self.db.commit()

            if int(dte.cash_amount) > 0:
                credit_note_dte = DteModel()
                credit_note_dte.branch_office_id = dte.branch_office_id
                credit_note_dte.cashier_id = 0
                credit_note_dte.dte_type_id = 61
                credit_note_dte.dte_version_id = 1
                credit_note_dte.status_id = 5
                credit_note_dte.chip_id = 0
                credit_note_dte.rut = '66666666-6'
                credit_note_dte.folio = folio
                credit_note_dte.denied_folio = dte.folio
                credit_note_dte.cash_amount = -abs(int(amount))
                credit_note_dte.card_amount = 0
                credit_note_dte.subtotal = -abs(round(int(amount)/1.19))
                credit_note_dte.tax = -abs(int(dte.cash_amount) - round(int(amount)/1.19))
                credit_note_dte.discount = 0
                credit_note_dte.total = -abs(int(amount))
                credit_note_dte.added_date = dte_date_detail
            else:
                credit_note_dte = DteModel()
                credit_note_dte.branch_office_id = dte.branch_office_id
                credit_note_dte.cashier_id = 0
                credit_note_dte.dte_type_id = 61
                credit_note_dte.dte_version_id = 1
                credit_note_dte.status_id = 5
                credit_note_dte.chip_id = 0
                credit_note_dte.rut = '66666666-6'
                credit_note_dte.folio = folio
                credit_note_dte.denied_folio = dte.folio
                credit_note_dte.cash_amount = 0
                credit_note_dte.card_amount = -abs(int(amount))
                credit_note_dte.subtotal = -abs(round(int(amount)/1.19))
                credit_note_dte.tax = -abs(int(dte.cash_amount) - round(int(amount)/1.19))
                credit_note_dte.discount = 0
                credit_note_dte.total = -abs(int(amount))
                credit_note_dte.added_date = dte_date_detail

            self.db.add(credit_note_dte)
            
            try:
                self.db.commit()

                folio_credit_note = FolioModel()
                folio_credit_note.folio = folio
                folio_credit_note.requested_status_id = 1
                folio_credit_note.used_status_id = 1
                folio_credit_note.billed_status_id = 1
                folio_credit_note.branch_office_id = dte.branch_office_id
                folio_credit_note.cashier_id = dte.cashier_id
                folio_credit_note.added_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                self.db.add(folio_credit_note)
                self.db.commit()

                self.create_account_asset(credit_note_dte)

                return {"status": "success", "message": "Credit Note saved successfully"}
            except Exception as e:
                self.db.rollback()
                return {"status": "error", "message": f"Error: {str(e)}"}
        else:
            return "Creditnote was not created"
        
    def create_account_asset(self, form_data):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        period_date = form_data.added_date.strftime("%Y-%m")

        american_date = str(period_date) + '-01'
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
        
    def generate_credit_note_ticket(self, folio, cash_amount, added_date):
        added_date = added_date.split("T")
        added_date = added_date[0]

        setting_data = SettingClass(self.db).get()
        token = setting_data["setting_data"]["simplefactura_token"]

        if int(cash_amount) > 0:
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
            
            print(2222222222222222323)

            url = f"https://api.simplefactura.cl/invoiceCreditDebitNotesV2/Casa_Matriz/6"

            headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
            
            response = requests.post(
                    url,
                    json=data,
                    headers=headers,
                )
            
            print(22222)
            
            data = json.loads(response.text)

            # Extraer el folio
            folio = data["data"]["folio"]

            return folio
        else:
            return None
