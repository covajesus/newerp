import requests
from app.backend.db.models import CustomerModel, WhatsappTemplateModel, BranchOfficeModel, UserModel
import os
from dotenv import load_dotenv
load_dotenv() 

class WhatsappClass:
    def __init__(self, db):
        self.db = db

    def send(self, dte_data, customer_rut): 
        customer = self.db.query(CustomerModel).filter(CustomerModel.rut == customer_rut).first()
        whatsapp_template = self.db.query(WhatsappTemplateModel).filter(WhatsappTemplateModel.id == 1).first()
        branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == dte_data.branch_office_id).first()
        user = self.db.query(UserModel).filter(UserModel.rut == branch_office.principal_supervisor).first()

        image = "https://jisbackend.com/files/" + str(dte_data.folio) + ".pdf"

        token = os.getenv('LIBREDTE_TOKEN')
        print(token)

        url = "https://graph.facebook.com/v20.0/101066132689690/messages"
        headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
        
        added_date_str = dte_data.added_date.strftime('%Y-%m-%d')

        print('Enviando mensaje de WhatsApp')

        required_fields = {
            "Tipo DTE": dte_data.dte_type_id,
            "Folio": dte_data.folio,
            "Fecha": added_date_str,
            "Total": dte_data.total,
            "Sucursal": branch_office.branch_office,
            "Supervisor": customer.customer,
            "Teléfono": customer.phone,
            "Email": customer.email
        }

        for label, value in required_fields.items():
            if value is None or str(value).strip() == "":
                raise ValueError(f"El campo '{label}' está vacío o no definido.")

        payload = {
                    "messaging_product": "whatsapp",
                    "to": f"{customer.phone}",
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
                                    {"type": "text", "text": str(dte_data.dte_type_id)},
                                    {"type": "text", "text": str(dte_data.folio)},
                                    {"type": "text", "text": added_date_str},
                                    {"type": "text", "text": str(dte_data.total)},
                                    {"type": "text", "text": branch_office.branch_office},
                                    {"type": "text", "text": customer.customer},
                                    {"type": "text", "text": customer.phone},
                                    {"type": "text", "text": customer.email},
                                ]
                            },
                            {
                                "type": "button",
                                "index": "0",
                                "sub_type": "url",
                                "parameters": [
                                    {"type": "text", "text": url}
                                ]
                            }
                        ]
                    }
                }

        response = requests.post(url, json=payload, headers=headers)

        print(response.text)
   