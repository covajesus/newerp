import requests
from app.backend.db.models import CustomerModel, WhatsappTemplateModel, BranchOfficeModel, UserModel

class WhatsappClass:
    def __init__(self, db):
        self.db = db

    def send(self, dte_data, customer_rut):
        customer = self.db.query(CustomerModel).filter(CustomerModel.rut == customer_rut).first()
        whatsapp_template = self.db.query(WhatsappTemplateModel).filter(WhatsappTemplateModel.id == 1).first()
        branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == dte_data.branch_office_id).first()
        user = self.db.query(UserModel).filter(UserModel.rut == branch_office.principal_supervisor).first()

        image = "https://www.dropbox.com/scl/fi/j8u57kwxt4usb0r29vj1f/prueba.pdf?rlkey=jxex87wvf2xr0062pc31uzg80&st=2247hchj&dl=0"

        url = "https://graph.facebook.com/v20.0/101066132689690/messages"
        headers = {
                    "Authorization": "Bearer EAAFYECjSEkQBALIHAvaWZBgoyZAQE21IdNlgjUuKf8CRY0DZAuJiLcnuZBRgjl4YGtN7YxGNvxpNjaeHH66VPeWqhjZBca3xMbI3DlZCh1qQCHHyCbw9dJaMvsIGa60vpxZAJ5m7QdwZAtwO71wPR68gSq0P9JeV50BDNgRzBqNYf0OocDMAVg2f",
                    "Content-Type": "application/json"
                }
        
        added_date_str = dte_data.added_date.strftime('%Y-%m-%d')

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
                                    {"type": "text", "text": url}
                                ]
                            }
                        ]
                    }
                }

        response = requests.post(url, json=payload, headers=headers)

        print(response)
   