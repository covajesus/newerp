from app.backend.db.models import HonoraryModel, EmployeeModel, EmployeeLaborDatumModel, UserModel, BranchOfficeModel, SupervisorModel, BankModel, RegionModel, CommuneModel, HonoraryReasonModel
from sqlalchemy import desc
from datetime import datetime
from app.backend.classes.hr_setting_class import HrSettingClass
from app.backend.classes.commune_class import CommuneClass
from app.backend.classes.helper_class import HelperClass
import requests
import json

class HonoraryClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, rut=None, rol_id=None, page=1, items_per_page=10):
        try:
            if rol_id == 3:
                data_query = self.db.query(HonoraryModel, EmployeeLaborDatumModel, BranchOfficeModel, SupervisorModel). \
                    outerjoin(EmployeeLaborDatumModel, EmployeeLaborDatumModel.rut == HonoraryModel.rut). \
                    outerjoin(BranchOfficeModel, BranchOfficeModel.id == EmployeeLaborDatumModel.branch_office_id). \
                    outerjoin(SupervisorModel, SupervisorModel.branch_office_id == BranchOfficeModel.id). \
                    filter(SupervisorModel.rut == rut). \
                    order_by(EmployeeModel.added_date.desc())
                
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
                    "rut": honorary.rut,
                    "full_name": honorary.full_name,
                    "nickname": honorary.nickname,
                    "reason": honorary.reason,
                    "start_date": honorary.start_date
                } for honorary, labor_datum, branch_office, supervisor in data]

            else:
                data_query = self.db.query(HonoraryModel) \
                                .join(HonoraryReasonModel, HonoraryReasonModel.id == HonoraryModel.reason_id) \
                                .join(UserModel, UserModel.rut == HonoraryModel.requested_by) \
                                .add_columns(
                                    HonoraryModel.status_id,
                                    HonoraryModel.id,
                                    HonoraryModel.rut,
                                    HonoraryModel.full_name,
                                    UserModel.nickname,
                                    HonoraryReasonModel.reason,
                                    HonoraryModel.added_date
                                ) \
                                .order_by(desc(HonoraryModel.added_date))

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
                    "rut": honorary.rut,
                    "full_name": honorary.full_name,
                    "nickname": honorary.nickname,
                    "reason": honorary.reason,
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
                "reason_id": data.reason_id,
                "branch_office_id": data.branch_office_id,
                "foreigner_id": data.foreigner_id,
                "bank_id": data.bank_id,
                "schedule_id": data.schedule_id,
                "region_id": data.region_id,
                "commune_id": data.commune_id,
                "requested_by": data.requested_by,
                "status_id": data.status_id,
                "accountability_status_id": data.accountability_status_id,
                "employee_to_replace": str(data.employee_to_replace),
                "rut": str(data.rut),
                "full_name": data.full_name,
                "email": data.email,
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
    
    def store(self, honorary_inputs):
        try:
            honorary = HonoraryModel()
            honorary.reason_id = honorary_inputs['reason_id']
            honorary.branch_office_id = honorary_inputs['branch_office_id']
            honorary.foreigner_id = honorary_inputs['foreigner_id']
            honorary.bank_id = honorary_inputs['bank_id']
            honorary.schedule_id = honorary_inputs['schedule_id']
            honorary.region_id = honorary_inputs['region_id']
            honorary.commune_id = honorary_inputs['commune_id']
            honorary.requested_by = honorary_inputs['requested_by']
            honorary.status_id = honorary_inputs['status_id']
            honorary.accountability_status_id = honorary_inputs['accountability_status_id']
            honorary.employee_to_replace = honorary_inputs['employee_to_replace']
            honorary.rut = honorary_inputs['rut']
            honorary.full_name = honorary_inputs['full_name']
            honorary.email = honorary_inputs['email']
            honorary.address = honorary_inputs['address']
            honorary.account_number = honorary_inputs['account_number']
            honorary.start_date = honorary_inputs['start_date']
            honorary.end_date = honorary_inputs['end_date']
            honorary.observation = honorary_inputs['observation']
            honorary.added_date = datetime.now()
            honorary.updated_date = datetime.now()

            self.db.add(honorary)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def generate(self, honorary_inputs):
        try:
            honorary = HonoraryModel()
            honorary.reason_id = honorary_inputs['reason_id']
            honorary.branch_office_id = honorary_inputs['branch_office_id']
            honorary.foreigner_id = honorary_inputs['foreigner_id']
            honorary.bank_id = honorary_inputs['bank_id']
            honorary.schedule_id = honorary_inputs['schedule_id']
            honorary.region_id = honorary_inputs['region_id']
            honorary.commune_id = honorary_inputs['commune_id']
            honorary.requested_by = honorary_inputs['requested_by']
            honorary.status_id = honorary_inputs['status_id']
            honorary.accountability_status_id = honorary_inputs['accountability_status_id']
            honorary.employee_to_replace = honorary_inputs['employee_to_replace']
            honorary.rut = honorary_inputs['rut']
            honorary.full_name = honorary_inputs['full_name']
            honorary.email = honorary_inputs['email']
            honorary.address = honorary_inputs['address']
            honorary.account_number = honorary_inputs['account_number']
            honorary.start_date = honorary_inputs['start_date']
            honorary.end_date = honorary_inputs['end_date']
            honorary.observation = honorary_inputs['observation']
            honorary.added_date = datetime.now()
            honorary.updated_date = datetime.now()

            self.db.add(honorary)
            self.db.commit()
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
        
    def update(self, id, honorary_inputs):
        honorary = self.db.query(HonoraryModel).filter(HonoraryModel.id == id).one_or_none()

        if honorary_inputs.reason_id != None:
            honorary.reason_id = honorary_inputs.reason_id

        if honorary_inputs.branch_office_id != None:
            honorary.branch_office_id = honorary_inputs.branch_office_id

        if honorary_inputs.foreigner_id != None:
            honorary.foreigner_id = honorary_inputs.foreigner_id

        if honorary_inputs.bank_id != None:
            honorary.bank_id = honorary_inputs.bank_id

        if honorary_inputs.schedule_id != None:
            honorary.schedule_id = honorary_inputs.schedule_id

        if honorary_inputs.region_id != None:
            honorary.region_id = honorary_inputs.region_id
        
        if honorary_inputs.commune_id != None:
            honorary.commune_id = honorary_inputs.commune_id

        if honorary_inputs.requested_by != None:
            honorary.requested_by = honorary_inputs.requested_by

        if honorary_inputs.status_id != None:
            honorary.status_id = honorary_inputs.status_id

        if honorary_inputs.accountability_status_id != None:
            honorary.accountability_status_id = honorary_inputs.accountability_status_id

        if honorary_inputs.employee_to_replace != None:
            honorary.employee_to_replace = honorary_inputs.employee_to_replace

        if honorary_inputs.rut != None:
            honorary.rut = honorary_inputs.rut

        if honorary_inputs.full_name != None:
            honorary.full_name = honorary_inputs.full_name

        if honorary_inputs.email != None:
            honorary.email = honorary_inputs.email

        if honorary_inputs.address != None:
            honorary.address = honorary_inputs.address

        if honorary_inputs.account_number != None:
            honorary.account_number = honorary_inputs.account_number

        if honorary_inputs.account_number != None:
            honorary.account_number = honorary_inputs.account_number

        if honorary_inputs.start_date != None:
            honorary.start_date = honorary_inputs.start_date

        if honorary_inputs.end_date != None:
            honorary.end_date = honorary_inputs.end_date

        if honorary_inputs.amount != None:
            amount = HelperClass().remove_from_string('.', str(honorary_inputs.amount))
            honorary.amount = amount

        if honorary_inputs.observation != None:
            honorary.observation = honorary_inputs.observation

        honorary.updated_date = datetime.now()

        self.db.add(honorary)
        
        try:
            self.db.commit()

            return 1
        except Exception as e:
            return 0
        
    # Función para emitir boleta de honorarios a SII 
    def send(self, data):
        hr_settings = HrSettingClass(self.db).get()

        commune = CommuneClass(self.db).get('id', data.commune_id)
        current_date = HelperClass().get_time_Y_m_d()
        
        amount = HelperClass().remove_from_string('.', str(data.amount))
        amount = round(int(amount) / float(hr_settings.percentage_honorary_bill))

        url = "https://apigateway.cl/api/v1/sii/bte/emitidas/emitir"

        payload = json.dumps({
                                "auth": {
                                    "pass": {
                                    "rut": "76063822-6",
                                    "clave": "JYM1"
                                    }
                                },
                                "boleta": {
                                    
                                    "Encabezado": {
                                        "IdDoc": {
                                            "FchEmis": current_date
                                        },
                                        "Emisor": {
                                            "RUTEmisor": '76063822-6'
                                        },
                                        "Receptor": {
                                            "RUTRecep": data.rut,
                                            "RznSocRecep": data.full_name,
                                            "DirRecep": data.address,
                                            "CmnaRecep": commune.commune
                                        }
                                    },
                                    "Detalle": [
                                        {
                                            "NmbItem": 'Boleta de Honorarios para ' + data.full_name,
                                            "MontoItem": amount
                                        }
                                    ]
                                }
                            })
        
        headers = {
            'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiYzdmNjkzMGM3Y2I3Mjg2N2ZlOTQwZDNlYzFjYTdkODgyNzIzNTNkYmIxNDczYzE1YzYwY2NiMWRiYmEzYTBlZmEwZTU5ZDY0ODYxNWY4OGEiLCJpYXQiOjE3MDU2MzI4NzQsIm5iZiI6MTcwNTYzMjg3NCwiZXhwIjo0ODYxMzA2NDc0LCJzdWIiOiI1NzYiLCJzY29wZXMiOltdfQ.D-TuweBtA_V271WltDeQYXvl8ohdz5JRNPBDMNvNQ3EQFXuqbJCUnDHwz5oLyHQZWfiho_3Sd7tMffkZMnGst8zS9Of3S5S4a677s8dDIrmhIds5qsTiXOhMCb6f3nZO8Ko5rw7HLjrmAp9GwezIOm22hU3rRmnzEIuP1KaLQoKq5xg35RA_iTwwDPG1AGIQS_5U0sRBTwGBr5gXa1WWLQuWitplI6cRZBJX1PWFdpzzGR-ZfFPbOPdbTAHG_wnZ0xH_nZCOL7jysV9S4a_3UKF57a3TKP9bXJqRww1r5hrxnw1pqdI-9w0MgE1snFprfWz_RsAWCw6ma767nXQn-DMDSK1y3FPxczHfVSF8gglSrKUmPzHkHs90jl0QYl1whK6wLoWv4gXxO7ZDKstTUZL1giBhcaiHiRv6JlWzUmwvKzVcsRdNw5Vw81CP6omONH4BFfxeyEHMsAlPncLRDWboNOYmGpztWZm5AuRBc1Mc9NaPFBj8yPgQPKGCC3Hsr8hx2s59O26oyhSc-hgA8dgj_sy5QoThz8T9zQXrcdSmNpfeK3D0B7fD4-VhQdDkr5rB9RqduLNyO6iHuB7JR54LpFKqWwIhQ7C_vMGLzhvMnKMz1mtd0567JgjF-xl0J-1OwryCWnM9kzUSOlRcoQV_kxPIqx-YxN_VTNPa0_c',
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        return 1