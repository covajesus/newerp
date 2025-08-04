import requests
from app.backend.db.models import CustomerModel, WhatsappTemplateModel, BranchOfficeModel, UserModel, DteModel
import os
from dotenv import load_dotenv
from datetime import datetime
load_dotenv() 

class WhatsappClass:
    def __init__(self, db):
        self.db = db

    def send(self, dte_data, customer_rut): 
        customer = self.db.query(CustomerModel).filter(CustomerModel.rut == customer_rut).first()
        whatsapp_template = self.db.query(WhatsappTemplateModel).filter(WhatsappTemplateModel.id == 1).first()
        branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == dte_data.branch_office_id).first()
        user = self.db.query(UserModel).filter(UserModel.rut == branch_office.principal_supervisor).first()

        image = "https://intrajisbackend.com/files/" + str(dte_data.folio) + ".pdf"

        token = os.getenv('LIBREDTE_TOKEN')

        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        created_dte_url = "https://libredte.cl/api/dte/dte_emitidos/info/"+ str(dte_data.dte_type_id) +"/"+ str(dte_data.folio) +"/76063822?getXML=0&getDetalle=0&getDatosDte=0&getTed=0&getResolucion=0&getEmailEnviados=0&getLinks=0&getReceptor=0&getSucursal=0&getUsuario=0"

        payload={}
        headers = {
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json"
                }

        created_dte_response = requests.request("GET", created_dte_url, headers=headers, data=payload)

        print(created_dte_response.text)
        data = created_dte_response.json()

        url_data = str(dte_data.dte_type_id) + '/' + str(dte_data.folio) + '/76063822/' + data['fecha'] + '/' + str(dte_data.total)
        url = "https://graph.facebook.com/v20.0/101066132689690/messages"

        headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
        
        added_date_str = dte_data.added_date.strftime('%d-%m-%Y')

        if dte_data.chip_id == 1:
            total = dte_data.total + 5000

        required_fields = {
            "Tipo DTE": dte_data.dte_type_id,
            "Folio": dte_data.folio,
            "Fecha": added_date_str,
            "Total": dte_data.total,
            "Sucursal": branch_office.branch_office,
            "Supervisor": user.full_name,
            "Teléfono": user.phone,
            "Email": user.email
        }

        for label, value in required_fields.items():
            if value is None or str(value).strip() == "":
                raise ValueError(f"El campo '{label}' está vacío o no definido.")
            
        if dte_data.dte_type_id == 39:
            dte_type = "boleta"
        else:
            dte_type = "factura"

        phone_str = str(customer.phone).strip()
        if not phone_str.startswith("56"):
            customer_phone = "56" + phone_str
        else:
            customer_phone = phone_str

        payload = {
                    "messaging_product": "whatsapp",
                    "to": f"{customer_phone}",
                    "type": "template",
                    "template": {
                        "name": whatsapp_template.title,
                        "language": {"code": "es"},
                        "components": [
                            {
                                "type": "header",
                                "parameters": [
                                    {
                                        "type": "document",
                                        "document": {
                                            "link": image,
                                            "filename": f"{dte_data.folio}.pdf"
                                        }
                                    }
                                ]
                            },
                            {
                                "type": "body",
                                "parameters": [
                                    {"type": "text", "text": str(dte_type)},
                                    {"type": "text", "text": str(dte_data.folio)},
                                    {"type": "text", "text": added_date_str},
                                    {"type": "text", "text": str(dte_data.total)},
                                    {"type": "text", "text": branch_office.branch_office},
                                    {"type": "text", "text": user.full_name},
                                    {"type": "text", "text": user.phone},
                                    {"type": "text", "text": user.email},
                                ]
                            },
                            {
                                "type": "button",
                                "index": "0",
                                "sub_type": "url",
                                "parameters": [
                                    {"type": "text", "text": url_data}
                                ]
                            }
                        ]
                    }
                }
        print(payload)
        response = requests.post(url, json=payload, headers=headers)

        print(response.text)
        
    def resend(self, dte_id, phone):
        dte_data = self.db.query(DteModel).filter(DteModel.id == dte_id).first()
        whatsapp_template = self.db.query(WhatsappTemplateModel).filter(WhatsappTemplateModel.id == 1).first()
        branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == dte_data.branch_office_id).first()
        user = self.db.query(UserModel).filter(UserModel.rut == branch_office.principal_supervisor).first()

        image = "https://intrajisbackend.com/files/" + str(dte_data.folio) + ".pdf"

        token = os.getenv('LIBREDTE_TOKEN')
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        created_dte_url = "https://libredte.cl/api/dte/dte_emitidos/info/"+ str(dte_data.dte_type_id) +"/"+ str(dte_data.folio) +"/76063822?getXML=0&getDetalle=0&getDatosDte=0&getTed=0&getResolucion=0&getEmailEnviados=0&getLinks=0&getReceptor=0&getSucursal=0&getUsuario=0"

        payload={}
        headers = {
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json"
                }

        created_dte_response = requests.request("GET", created_dte_url, headers=headers, data=payload)

        print(created_dte_response.text)
        data = created_dte_response.json()

        url_data = str(dte_data.dte_type_id) + '/' + str(dte_data.folio) + '/76063822/' + data['fecha'] + '/' + str(dte_data.total)
    
        url = "https://graph.facebook.com/v20.0/101066132689690/messages"

        headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            
        added_date_str = dte_data.added_date.strftime('%d-%m-%Y')
                
        if dte_data.dte_type_id == 39:
            dte_type = "boleta"
        else:
            dte_type = "factura"

        phone_str = str(phone).strip()
        if not phone_str.startswith("56"):
            customer_phone = "56" + phone_str
        else:
            customer_phone = phone_str

        if user:
            payload = {
                        "messaging_product": "whatsapp",
                        "to": f"{customer_phone}",
                        "type": "template",
                        "template": {
                            "name": whatsapp_template.title,
                            "language": {"code": "es"},
                            "components": [
                                {
                                    "type": "header",
                                    "parameters": [
                                        {
                                            "type": "document",
                                            "document": {
                                                "link": image,
                                                "filename": f"{dte_data.folio}.pdf"
                                            }
                                        }
                                    ]
                                },
                                {
                                    "type": "body",
                                    "parameters": [
                                        {"type": "text", "text": str(dte_type)},
                                        {"type": "text", "text": str(dte_data.folio)},
                                        {"type": "text", "text": added_date_str},
                                        {"type": "text", "text": str(dte_data.total)},
                                        {"type": "text", "text": branch_office.branch_office},
                                        {"type": "text", "text": user.full_name},
                                        {"type": "text", "text": user.phone},
                                        {"type": "text", "text": user.email},
                                    ]
                                },
                                {
                                    "type": "button",
                                    "index": "0",
                                    "sub_type": "url",
                                    "parameters": [
                                        {"type": "text", "text": url_data}
                                    ]
                                }
                            ]
                        }
                    }
        print(payload)
        response = requests.post(url, json=payload, headers=headers)

        print(response.text)

    def cron_to_resend(self):
        dtes = self.db.query(DteModel).filter(DteModel.status_id == 4).filter(DteModel.dte_type_id == 33).filter(DteModel.dte_version_id == 1).filter(DteModel.period == '2025-08').all()
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        save_path = "C:/Users/jesus/OneDrive/Desktop/escritorio/newerp/files"

        for dte in dtes:
            url = "https://libredte.cl/api/dte/dte_emitidos/pdf/33/"+ str(dte.folio) +"/76063822?formato=general&papelContinuo=0&copias_tributarias=1&copias_cedibles=1&cedible=0&compress=0&base64=0"

            payload={}
            headers = {
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json"
                }

            response = requests.request("GET", url, headers=headers, data=payload)

            if response.status_code == 200:
                file_path = os.path.join(save_path, f"{dte.folio}.pdf")
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"✅ Guardado: {file_path}")
            else:
                print(f"❌ Error al 2")
    
    def notify_paymeent(self, folio):
        dte = self.db.query(DteModel).filter(DteModel.folio == folio).first()
        customer = self.db.query(CustomerModel).filter(CustomerModel.rut == dte.rut).first()
        branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == dte.branch_office_id).first()
        user = self.db.query(UserModel).filter(UserModel.rut == branch_office.principal_supervisor).first()
        phone = user.phone
        whatsapp_template = self.db.query(WhatsappTemplateModel).filter(WhatsappTemplateModel.id == 2).first()

        token = os.getenv('LIBREDTE_TOKEN')

        url = "https://graph.facebook.com/v20.0/101066132689690/messages"

        headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
        
        phone_str = str(phone).strip()
        if not phone_str.startswith("56"):
            customer_phone = "56" + phone_str
        else:
            customer_phone = phone_str

        payload = {
                    "messaging_product": "whatsapp",
                    "to": f"{customer_phone}",
                    "type": "template",
                    "template": {
                        "name": whatsapp_template.title,
                        "language": {
                            "code": "es"
                        },
                        "components": [
                            {
                                "type": "body",
                                "parameters": [
                                    {"type": "text", "text": user.full_name},
                                    {"type": "text", "text": str(folio)},
                                    {"type": "text", "text": str(dte.rut)},
                                    {"type": "text", "text": customer.customer},
                                    {"type": "text", "text": branch_office.branch_office},
                                    {"type": "text", "text": str(dte.total)},
                                    {"type": "text", "text": datetime.strptime(dte.payment_date, '%Y-%m-%d').strftime('%d-%m-%Y')},
                                ]
                            }
                        ]
                    }
                }

        print(payload)
        response = requests.post(url, json=payload, headers=headers)

        print(response.text)