from app.backend.db.models import FolioModel, CashierModel, FolioReportModel, FolioQuantityPerCashierModel
from app.backend.classes.setting_class import SettingClass
from app.backend.classes.alert_class import AlertClass
import json
import requests
import pytz
import datetime

class FolioClass:
    def __init__(self, db):
        self.db = db

    # Funcion para obtener a todos los folios con paginacion
    def get_all(self, page=0, items_per_page=10):
        try:
            if page != 0:
                data_query = self.db.query(FolioModel.id, FolioModel.folio, FolioModel.billed_status_id, FolioModel.branch_office_id, FolioModel.cashier_id, FolioModel.requested_status_id, FolioModel.used_status_id, FolioModel.added_date). \
                        order_by(FolioModel.folio)

                total_items = data_query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return "Invalid page number"

                data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return "No data found"

                serialized_data = [{
                        "id": folio.id,
                        "folio": folio.folio,
                        "branch_office_id": folio.branch_office_id,
                        "cashier_id": folio.cashier_id,
                        "billed_status_id": folio.billed_status_id,
                        "requested_status_id": folio.requested_status_id,
                        "used_status_id": folio.used_status_id,
                        "added_date": folio.added_date,
                    } for folio in data]

                total_available_receipts = self.db.query(FolioModel).filter(FolioModel.requested_status_id == 0).count()
                print(total_available_receipts)
                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data,
                    "total_available_receipts": total_available_receipts
                }
            else:
                data_query = self.db.query(FolioModel.id, FolioModel.folio, FolioModel.branch_office_id, FolioModel.cashier_id, FolioModel.requested_status_id, FolioModel.used_status_id). \
                        order_by(FolioModel.folio).all()

                serialized_data = [{
                        "id": folio.id,
                        "folio": folio.folio,
                        "branch_office_id": folio.branch_office_id,
                        "cashier_id": folio.cashier_id,
                        "requested_status_id": folio.requested_status_id,
                        "used_status_id": folio.used_status_id,
                    } for folio in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def report(self):
        folio_reports = self.db.query(FolioReportModel).all()

        if not folio_reports:
            return "No hay folios en el informe."
        
        serialized_data = []
        for folio_report in folio_reports:
            folio_report_dict = {
                "id": folio_report.id,
                "cashier": folio_report.cashier,
                "branch_office": folio_report.branch_office,
                "available_folios": folio_report.available_folios,
                "rustdesk": folio_report.rustdesk,
                "anydesk": folio_report.anydesk
            }
            serialized_data.append(folio_report_dict)

        return json.dumps(serialized_data)
    
    def get_quantity_per_cashier(self):
        folio_reports = self.db.query(FolioQuantityPerCashierModel).all()

        if not folio_reports:
            return "No hay folios en el informe."
        
        serialized_data = []
        for folio_report in folio_reports:
            folio_report_dict = {
                "id": folio_report.id,
                "cashier": folio_report.cashier,
                "branch_office": folio_report.branch_office,
                "available_folios": folio_report.available_folios,
                "rustdesk": folio_report.rustdesk,
                "anydesk": folio_report.anydesk
            }
            serialized_data.append(folio_report_dict)

        return json.dumps(serialized_data)
    
    def validate(self):
        try:
            folio_count = self.db.query(FolioModel).filter(FolioModel.requested_status_id == 0).count()
            
            if folio_count < 100:
                return 1  # Retorna 1 si hay menos de 100 folios
            else:
                return 0  # Retorna 0 si hay 100 o más folios
        
        except Exception as e:
            # Captura cualquier error y retorna el mensaje de error
            error_message = str(e)
            return f"Error: {error_message}"
        
    def assignation(self, folio, branch_office_id, cashier_id):
        try:
            # Consulta de folios disponibles
            folio_count = self.db.query(FolioModel).filter(FolioModel.folio == folio).filter(FolioModel.branch_office_id == branch_office_id).filter(FolioModel.cashier_id == cashier_id).count()
            
            # Valida si el conteo es menor a 100
            if folio_count > 0:
                return 1  # Retorna 1 si hay menos de 100 folios
            else:
                return 0  # Retorna 0 si hay 100 o más folios
        
        except Exception as e:
            # Captura cualquier error y retorna el mensaje de error
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get_folio(self, branch_office_id, cashier_id, requested_quantity, quantity_in_cashier):
        try:
            if requested_quantity > 0:
                # Consulta de cajero para obtener el folio_segment_id
                cashier = self.db.query(CashierModel).filter(CashierModel.id == cashier_id).first()

                if not cashier:
                    return "Cajero no encontrado."

                # Consulta para obtener el folio disponible (limitado a 1 folio)
                query = self.db.query(FolioModel).filter(FolioModel.requested_status_id == 0)

                if cashier.folio_segment_id == 0:
                    query = query.filter(FolioModel.folio_segment_id == 0)
                else:
                    query = query.filter(FolioModel.folio_segment_id == cashier.folio_segment_id)

                # Obtener un solo folio disponible
                folio = query.first()

                if not folio:
                    return "No hay folios disponibles con el estado solicitado."

                # Actualizar el folio directamente
                folio.branch_office_id = branch_office_id
                folio.cashier_id = cashier_id
                folio.requested_status_id = 1

                # Confirmar los cambios en la base de datos
                self.db.commit()

                # Serialización del folio actualizado
                folio_dict = {
                    "id": folio.id,
                    "folio": folio.folio,
                    "branch_office_id": folio.branch_office_id,
                    "cashier_id": folio.cashier_id,
                    "requested_status_id": folio.requested_status_id,
                }

                return json.dumps(folio_dict)
            else:
                return "La cantidad solicitada debe ser mayor a 0."
        except Exception as e:
            # Captura cualquier error y retorna el mensaje de error
            return f"Error: {str(e)}"
    
    def validate_caf_limit(self, folio_segment_id):
        try:

            if folio_segment_id != 9:
                settings = SettingClass(self.db).get()
                if settings:
                    folios = self.db.query(FolioModel).filter(FolioModel.requested_status_id == 0).filter(FolioModel.folio_segment_id == folio_segment_id).count()
                    caf_limit = settings['setting_data']['caf_limit']

                    if folios < caf_limit:
                        return 1
                    else:
                        return 0
                else:
                    return 3
            else:
                return 0
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get(self, branch_office_id, cashier_id, requested_quantity, quantity_in_cashier):
        try:
            if requested_quantity > 0:
                cashier = self.db.query(CashierModel).filter(CashierModel.id == cashier_id).limit(1).first()
                cashier.available_folios = quantity_in_cashier
                self.db.add(cashier)
                self.db.commit()
            
                response_validate_caf_limit = self.validate_caf_limit(cashier.folio_segment_id)

                if response_validate_caf_limit == 1:
                    AlertClass(self.db).send_email(1, cashier.folio_segment_id)

                folios = self.db.query(FolioModel).filter(FolioModel.requested_status_id == 0).filter(FolioModel.folio_segment_id == cashier.folio_segment_id).limit(1).all()

                # Verifica si hay folios disponibles
                if not folios:
                    return "No hay folios disponibles con el estado solicitado."

                # Procesa cada folio y actualiza sus valores
                for folio in folios:
                    folio.branch_office_id = branch_office_id
                    folio.cashier_id = cashier_id
                    folio.requested_status_id = 1
                    tz = pytz.timezone('America/Santiago')
                    current_date = datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                    folio.updated_date = current_date
                    self.db.add(folio)
                
                # Confirma todos los cambios después de procesar los folios
                self.db.commit()
                
                # Serialización de los folios actualizados
                serialized_data = []
                for folio in folios:
                    folio_dict = {
                        "id": folio.id,
                        "folio": folio.folio,
                        "branch_office_id": folio.branch_office_id,
                        "cashier_id": folio.cashier_id,
                        "requested_status_id": folio.requested_status_id,
                        # Agrega otros campos necesarios según el modelo FolioModel
                    }
                    serialized_data.append(folio_dict)
                
                return json.dumps(serialized_data)
            else:
                return "La cantidad solicitada debe ser mayor a 0."
        
        except Exception as e:
            # Captura cualquier error y retorna el mensaje de error
            error_message = str(e)
            return f"Error: {error_message}"

    def update(self, folio):
        folio_count = self.db.query(FolioModel).filter(FolioModel.folio == folio).count()
        if folio_count > 0:
            folio = self.db.query(FolioModel).filter(FolioModel.folio == folio).first()
            folio.used_status_id = 1
            self.db.add(folio)
            self.db.commit()

            return "Folio updated successfully"
        else:
            return "Folio not found"

    def update_billed_ticket(self, folio):
        folio_record = self.db.query(FolioModel).filter(FolioModel.folio == folio).first()
        
        if folio_record:
            folio_record.billed_status_id = 1
            self.db.commit()
            return f"Folio {folio} updated successfully"
        
        return "Folio not found"

    def request(self, amount):
        payload = {
            "credenciales": {
                "rutEmisor": "76063822-6",
                "nombreSucursal": "Casa Matriz"   
            },
            "codigoTipoDte": 39,
            "ambiente": 1
        }

        headers = {
            'Authorization': 'Basic cm9kcmlnb2NhYmV6YXNAamlzcGFya2luZy5jb206Um9ybzIwMjQu',
            'Content-Type': 'application/json'
        }

        response = requests.post(
            'https://api.simplefactura.cl/folios/consultar',
            data=json.dumps(payload),
            headers=headers
        )

        response_data = response.json()

        if response_data.get('status') == 200:
            data = response_data.get('data')

            quantity = len(data)

            if quantity > 0:
                folio_data = self.db.query(FolioModel).order_by(FolioModel.id.desc()).first()

                last_row = data[-1]

                available_caf_folios = last_row['hasta'] - folio_data.folio

                print(available_caf_folios)

                if available_caf_folios >= amount:
                    last_registered_folio = folio_data.folio
                    last_registered_folio += 1
                    for i in range(last_registered_folio, last_registered_folio + 1):
                        print(i)
                else:
                    return "No hay folios disponibles en el CAF"