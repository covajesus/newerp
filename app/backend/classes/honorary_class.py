from app.backend.db.models import HonoraryModel, EmployeeModel, EmployeeLaborDatumModel, UserModel, BranchOfficeModel, SupervisorModel, BankModel, RegionModel, CommuneModel, HonoraryReasonModel
from sqlalchemy import desc
from datetime import datetime
from app.backend.classes.setting_class import SettingClass
from app.backend.classes.commune_class import CommuneClass
from app.backend.classes.region_class import RegionClass
from app.backend.classes.authentication_class import AuthenticationClass
from app.backend.classes.helper_class import HelperClass
import requests
import json
from sqlalchemy import func

class HonoraryClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, search_branch_office_id=None, search_rut=None, rut=None, rol_id=None, page=1, items_per_page=10):

        try:
            filters = []
            if search_branch_office_id is not None:
                filters.append(HonoraryModel.branch_office_id == search_branch_office_id)

            if search_rut is not None and search_rut != '':
                filters.append(HonoraryModel.replacement_employee_rut == search_rut)

            print(rol_id)

            if rol_id == 1 or rol_id == 2 or rol_id == 5:
                data_query = self.db.query(HonoraryModel.status_id, HonoraryModel.id, UserModel.full_name, HonoraryReasonModel.honorary_reason, HonoraryModel.replacement_employee_rut, HonoraryModel.replacement_employee_full_name, HonoraryModel.added_date). \
                    outerjoin(BranchOfficeModel, BranchOfficeModel.id == HonoraryModel.branch_office_id). \
                    outerjoin(HonoraryReasonModel, HonoraryReasonModel.id == HonoraryModel.honorary_reason_id). \
                    outerjoin(UserModel, UserModel.rut == HonoraryModel.requested_by). \
                    filter(
                        *filters
                    ).order_by(HonoraryModel.added_date.desc())
                
                data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()
                total_items = data_query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return "Invalid page number"

                if not data:
                    return "No data found"

                serialized_data = [{
                    "status_id": honorary.status_id,
                    "id": honorary.id,
                    "requested_by": honorary.full_name,
                    "honorary_reason": honorary.honorary_reason,
                    "replacement_employee_rut": honorary.replacement_employee_rut,
                    "replacement_employee_full_name": honorary.replacement_employee_full_name,
                    "added_date": honorary.added_date
                } for honorary in data]

            else:
                data_query = self.db.query(HonoraryModel.status_id, HonoraryModel.id, UserModel.full_name, HonoraryReasonModel.honorary_reason, HonoraryModel.replacement_employee_rut, HonoraryModel.replacement_employee_full_name, HonoraryModel.added_date). \
                    outerjoin(BranchOfficeModel, BranchOfficeModel.id == HonoraryModel.branch_office_id). \
                    outerjoin(HonoraryReasonModel, HonoraryReasonModel.id == HonoraryModel.honorary_reason_id). \
                    outerjoin(UserModel, UserModel.rut == HonoraryModel.requested_by). \
                    filter(HonoraryModel.requested_by == rut). \
                    filter(
                        *filters
                    ).order_by(HonoraryModel.added_date.desc())

                data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()
                total_items = data_query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return "Invalid page number"

                if not data:
                    return "No data found"

                # Serializar los datos
                serialized_data = [{
                    "status_id": honorary.status_id,
                    "id": honorary.id,
                    "requested_by": honorary.full_name,
                    "honorary_reason": honorary.honorary_reason,
                    "replacement_employee_rut": honorary.replacement_employee_rut,
                    "replacement_employee_full_name": honorary.replacement_employee_full_name,
                    "added_date": honorary.added_date
                } for honorary in data]

            return {
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "items_per_page": items_per_page,
                "data": serialized_data
            }

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    
    def get(self, field, value):
        try:
            data = self.db.query(HonoraryModel).filter(getattr(HonoraryModel, field) == value).first()

            serialized_data = {
                "honorary_reason_id": data.honorary_reason_id,
                "branch_office_id": data.branch_office_id,
                "foreigner_id": data.foreigner_id,
                "bank_id": data.bank_id,
                "account_type_id": data.account_type_id,
                "schedule_id": data.schedule_id,
                "region_id": data.region_id,
                "commune_id": data.commune_id,
                "requested_by": data.requested_by,
                "status_id": data.status_id,
                "employee_to_replace": str(data.employee_to_replace),
                "replacement_employee_rut": str(data.replacement_employee_rut),
                "replacement_employee_full_name": data.replacement_employee_full_name,
                "address": str(data.address),
                "account_number": str(data.account_number),
                "start_date": str(data.start_date),
                "end_date": str(data.end_date),
                "amount": str(data.amount),
                "observation": str(data.observation),
            }

            return json.dumps(serialized_data)

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, requested_by, honorary_inputs):
        try:
            honorary = HonoraryModel()
            honorary.honorary_reason_id = honorary_inputs.honorary_reason_id
            honorary.branch_office_id = honorary_inputs.branch_office_id
            honorary.foreigner_id = honorary_inputs.foreigner_id
            honorary.bank_id = honorary_inputs.bank_id
            honorary.schedule_id = honorary_inputs.schedule_id
            honorary.region_id = honorary_inputs.region_id
            honorary.commune_id = honorary_inputs.commune_id
            honorary.account_type_id = honorary_inputs.account_type_id
            honorary.requested_by = requested_by
            honorary.status_id = 14
            honorary.employee_to_replace = honorary_inputs.employee_to_replace
            honorary.replacement_employee_rut = honorary_inputs.replacement_employee_rut
            honorary.replacement_employee_full_name = honorary_inputs.replacement_employee_full_name
            honorary.email = honorary_inputs.email
            honorary.address = honorary_inputs.address
            honorary.account_number = honorary_inputs.account_number
            if honorary_inputs.start_date != 'None' and honorary_inputs.start_date != None:
                honorary.start_date = honorary_inputs.start_date
            if honorary_inputs.end_date != 'None' and honorary_inputs.end_date != None:
                honorary.end_date = honorary_inputs.end_date
            honorary.observation = honorary_inputs.observation
            honorary.amount = honorary_inputs.amount
            honorary.added_date = datetime.now()
            honorary.updated_date = datetime.now()

            self.db.add(honorary)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def generate(self, id, honorary_inputs):
        try:
            honorary = self.db.query(HonoraryModel).filter(HonoraryModel.id == id).first()
            honorary.honorary_reason_id = honorary_inputs.honorary_reason_id
            honorary.branch_office_id = honorary_inputs.branch_office_id
            honorary.foreigner_id = honorary_inputs.foreigner_id
            honorary.bank_id = honorary_inputs.bank_id
            honorary.schedule_id = honorary_inputs.schedule_id
            honorary.region_id = honorary_inputs.region_id
            honorary.commune_id = honorary_inputs.commune_id
            honorary.account_type_id = honorary_inputs.account_type_id
            honorary.status_id = 2
            honorary.employee_to_replace = honorary_inputs.employee_to_replace
            honorary.replacement_employee_rut = honorary_inputs.replacement_employee_rut
            honorary.replacement_employee_full_name = honorary_inputs.replacement_employee_full_name
            honorary.email = honorary_inputs.email
            honorary.address = honorary_inputs.address
            honorary.account_number = honorary_inputs.account_number
            if honorary_inputs.start_date != 'None' and honorary_inputs.start_date != None:
                honorary.start_date = honorary_inputs.start_date
            if honorary_inputs.end_date != 'None' and honorary_inputs.end_date != None:
                honorary.end_date = honorary_inputs.end_date
            honorary.observation = honorary_inputs.observation
            honorary.amount = honorary_inputs.amount
            honorary.added_date = datetime.now()
            honorary.updated_date = datetime.now()

            self.db.add(honorary)
            self.db.commit()

            if honorary_inputs.foreigner_id == 1:
                self.send(honorary_inputs)

            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(HonoraryModel).filter(HonoraryModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def validate(self, data):
        data = self.db.query(HonoraryModel).filter(HonoraryModel.replacement_employee_rut == data.replacement_employee_rut).filter(func.date(HonoraryModel.added_date) == str(data.added_date)[:10]).count()
            
        return data
    
    def impute(self, form_data):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        honorary = self.db.query(HonoraryModel).filter(HonoraryModel.id == form_data.id).first()
        settings = SettingClass(self.db).get()
        
        american_date = form_data.period + '-01'
        utf8_date = HelperClass.convert_to_utf8(american_date)
        expense_type = '443000344'
        branch_office = self.db.query(BranchOfficeModel).filter(
            BranchOfficeModel.id == honorary.branch_office_id
        ).first()

        gloss = (
                branch_office.branch_office
                + "_"
                + expense_type
                + "_"
                + utf8_date
                + "_Honorario_"
                + str(form_data.id)
            )
        gross_amount = HelperClass().remove_from_string('.', str(honorary.amount))
        gross_amount = round(int(gross_amount) / float(settings["setting_data"]["percentage_honorary_bill"]))
        tax = int(gross_amount) - int(honorary.amount)
        net_amount = round(gross_amount - tax)
        
        data = {
                "fecha": american_date,
                "glosa": gloss,
                "detalle": {
                    "debe": {
                        111000102: gross_amount
                    },
                    "haber": {
                        expense_type: net_amount,
                        "221000223": tax,
                    }
                },
                "operacion": "I",
                "documentos": {
                    "emitidos": [
                        {
                            "dte": '',
                            "folio": '',
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

        honorary = self.db.query(HonoraryModel).filter(HonoraryModel.id == form_data.id).first()
        honorary.status_id = 15
        honorary.updated_date = datetime.now()

        self.db.add(honorary)
        self.db.commit()

        return "Accounting entry created successfully"

        
    def send(self, data):
        settings = SettingClass(self.db).get()
        commune = CommuneClass(self.db).get('id', data.commune_id)
        region = RegionClass(self.db).get('id', data.region_id)
        
        # Obtener fecha actual en formato DD-MM-YYYY para Simple Factura
        current_date_y_m_d = HelperClass().get_time_Y_m_d()  # Formato YYYY-MM-DD
        # Convertir a DD-MM-YYYY
        date_parts = current_date_y_m_d.split('-')
        current_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
        
        amount = HelperClass().remove_from_string('.', str(data.amount))
        amount = round(int(amount) / float(settings["setting_data"]["percentage_honorary_bill"]))

        # Verificar y renovar token si es necesario
        check_token_status = AuthenticationClass(self.db).check_simplefactura_token()
        if check_token_status == 0:
            print('El token de Simple Factura está vencido, renovando...')
            AuthenticationClass(self.db).create_simplefactura_token()
        
        # Obtener token actualizado
        updated_settings = SettingClass(self.db).get()
        token = updated_settings["setting_data"]["simplefactura_token"]

        url = "https://api.simplefactura.cl/bhe/emitir"

        payload = {
            "RutEmisor": "76063822-6",
            "Retencion": 1,
            "FechaEmision": current_date,
            "Emisor": {
                "Direccion": "0"
            },
            "Receptor": {
                "Rut": data.replacement_employee_rut,
                "Nombre": data.replacement_employee_full_name,
                "Direccion": data.address,
                "Region": region.simplefactura_region_code,
                "Comuna": commune.commune if commune else "No especificada"
            },
            "Detalles": [
                {
                    "Nombre": f"Boleta de Honorarios para {data.replacement_employee_full_name}",
                    "Valor": amount
                }
            ]
        }

        print(payload)
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")

            if response.status_code == 200:
                print("Boleta de honorarios emitida exitosamente en Simple Factura")
                return 1
            else:
                print(f"Error al emitir boleta de honorarios: {response.status_code} - {response.text}")
                return 0
                
        except Exception as e:
            print(f"Error de conexión con Simple Factura: {str(e)}")
            return 0

    def get_data_by_rut(self, rut):
        """
        Busca si el usuario con el RUT dado tiene boletas de honorarios 
        y devuelve la más próxima (próxima fecha de inicio)
        """
        try:
            # Buscar honorarios para el RUT dado que estén activos y con fecha futura
            current_date = datetime.now().date()
            
            honorary = self.db.query(
                HonoraryModel.id,
                HonoraryModel.honorary_reason_id,
                HonoraryModel.branch_office_id,
                HonoraryModel.foreigner_id,
                HonoraryModel.bank_id,
                HonoraryModel.schedule_id,
                HonoraryModel.region_id,
                HonoraryModel.commune_id,
                HonoraryModel.account_type_id,
                HonoraryModel.requested_by,
                HonoraryModel.status_id,
                HonoraryModel.employee_to_replace,
                HonoraryModel.replacement_employee_rut,
                HonoraryModel.address,
                HonoraryModel.account_number,
                HonoraryModel.start_date,
                HonoraryModel.end_date,
                HonoraryModel.email,
                HonoraryModel.amount,
                HonoraryModel.observation,
                HonoraryModel.replacement_employee_full_name,
                HonoraryReasonModel.honorary_reason,
            ).outerjoin(
                HonoraryReasonModel, HonoraryReasonModel.id == HonoraryModel.honorary_reason_id
            ).filter(
                HonoraryModel.replacement_employee_rut == rut,
                HonoraryModel.start_date >= current_date,  # Solo fechas futuras o actuales
                HonoraryModel.status_id.in_([1, 2, 3])  # Estados activos (ajustar según tu lógica)
            ).order_by(
                HonoraryModel.start_date.asc()  # La más próxima primero
            ).first()

            if honorary:
                return {
                    "status": "found",
                    "data": {
                        "id": honorary.id,
                        "honorary_reason_id": honorary.honorary_reason_id,
                        "branch_office_id": honorary.branch_office_id,
                        "foreigner_id": honorary.foreigner_id,
                        "bank_id": honorary.bank_id,
                        "schedule_id": honorary.schedule_id,
                        "region_id": honorary.region_id,
                        "commune_id": honorary.commune_id,
                        "account_type_id": honorary.account_type_id,
                        "requested_by": honorary.requested_by,
                        "replacement_employee_rut": honorary.replacement_employee_rut,
                        "replacement_employee_full_name": honorary.replacement_employee_full_name,
                        "address": honorary.address,
                        "account_number": honorary.account_number,
                        "start_date": honorary.start_date.strftime("%Y-%m-%d") if honorary.start_date else None,
                        "end_date": honorary.end_date.strftime("%Y-%m-%d") if honorary.end_date else None,
                        "email": honorary.email,
                        "amount": honorary.amount,
                        "status_id": honorary.status_id,
                        "observation": honorary.observation,
                        "honorary_reason": honorary.honorary_reason
                    }
                }
            else:
                # Si no encontró honorarios futuros, buscar el más reciente
                last_honorary = self.db.query(
                    HonoraryModel.id,
                    HonoraryModel.honorary_reason_id,
                    HonoraryModel.branch_office_id,
                    HonoraryModel.foreigner_id,
                    HonoraryModel.bank_id,
                    HonoraryModel.schedule_id,
                    HonoraryModel.region_id,
                    HonoraryModel.commune_id,
                    HonoraryModel.account_type_id,
                    HonoraryModel.requested_by,
                    HonoraryModel.status_id,
                    HonoraryModel.employee_to_replace,
                    HonoraryModel.replacement_employee_rut,
                    HonoraryModel.address,
                    HonoraryModel.account_number,
                    HonoraryModel.start_date,
                    HonoraryModel.end_date,
                    HonoraryModel.email,
                    HonoraryModel.amount,
                    HonoraryModel.observation,
                    HonoraryModel.replacement_employee_full_name,
                    HonoraryReasonModel.honorary_reason,
                ).outerjoin(
                    HonoraryReasonModel, HonoraryReasonModel.id == HonoraryModel.honorary_reason_id
                ).filter(
                    HonoraryModel.replacement_employee_rut == rut
                ).order_by(
                    HonoraryModel.start_date.desc()  # El más reciente primero
                ).first()

                if last_honorary:
                    return {
                        "status": "found_past",
                        "data": {
                            "id": last_honorary.id,
                            "honorary_reason_id": last_honorary.honorary_reason_id,
                            "branch_office_id": last_honorary.branch_office_id,
                            "foreigner_id": last_honorary.foreigner_id,
                            "bank_id": last_honorary.bank_id,
                            "schedule_id": last_honorary.schedule_id,
                            "region_id": last_honorary.region_id,
                            "commune_id": last_honorary.commune_id,
                            "account_type_id": last_honorary.account_type_id,
                            "requested_by": last_honorary.requested_by,
                            "replacement_employee_rut": last_honorary.replacement_employee_rut,
                            "replacement_employee_full_name": last_honorary.replacement_employee_full_name,
                            "address": last_honorary.address,
                            "account_number": last_honorary.account_number,
                            "start_date": last_honorary.start_date.strftime("%Y-%m-%d") if last_honorary.start_date else None,
                            "end_date": last_honorary.end_date.strftime("%Y-%m-%d") if last_honorary.end_date else None,
                            "email": last_honorary.email,
                            "amount": last_honorary.amount,
                            "status_id": last_honorary.status_id,
                            "observation": last_honorary.observation,
                            "honorary_reason": last_honorary.honorary_reason
                        }
                    }
                else:
                    return {
                        "status": "not_found",
                        "message": "No se encontraron boletas de honorarios para este RUT"
                    }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error al buscar honorarios: {str(e)}"
            }