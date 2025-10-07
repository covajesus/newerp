import requests
from app.backend.db.models import CustomerModel, MovementModel, WhatsappTemplateModel, BranchOfficeModel, UserModel, DteModel, CapitulationModel, ExpenseTypeModel, MovementProductModel, ProductModel
import os
from dotenv import load_dotenv
from datetime import datetime
import json
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
        
        # Devolver la respuesta del envío de WhatsApp
        try:
            response_data = response.json()
            return {
                "status": "success" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "response": response_data,
                "whatsapp_accepted": "accepted" if response.status_code == 200 else "rejected"
            }
        except Exception as e:
            return {
                "status": "error",
                "status_code": response.status_code,
                "response": response.text,
                "error": str(e),
                "whatsapp_accepted": "rejected"
            }

    def movements(self, movement_id):
        movement = self.db.query(MovementModel).filter(MovementModel.id == movement_id).first()
        branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == movement.branch_office_id).first()
        user = self.db.query(UserModel).filter(UserModel.rut == branch_office.principal_supervisor).first()
        whatsapp_template = self.db.query(WhatsappTemplateModel).filter(WhatsappTemplateModel.id == 4).first()
        
        # Obtener los productos del movimiento
        movement_products = self.db.query(MovementProductModel, ProductModel).join(
            ProductModel, ProductModel.id == MovementProductModel.product_id
        ).filter(MovementProductModel.movement_id == movement_id).all()
        
        # Crear lista de nombres de productos separados por coma
        products = ", ".join([product_model.description for movement_product, product_model in movement_products])
        
        phone = user.phone  # Ej: '912345678'
        supervisor_name = user.full_name
        movement_id = movement.id

        # URL de la API
        url = 'https://graph.facebook.com/v20.0/101066132689690/messages'

        token = os.getenv('LIBREDTE_TOKEN')

        # Cabeceras
        headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }

        phone_str = str(phone).strip()
        if not phone_str.startswith("56"):
            phone = "56" + phone_str
        else:
            phone = phone_str

        # Payload en formato JSON
        payload = {
            "messaging_product": "whatsapp",
            "to": f"{phone}",
            "type": "template",
            "template": {
                "name": whatsapp_template.title,
                "language": {"code": "es"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": str(supervisor_name)},
                            {"type": "text", "text": str(movement_id)},
                            {"type": "text", "text": str(products)}
                        ]
                    }
                ]
            }
        }

        print(payload)

        # Enviar la solicitud POST
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        # Mostrar la respuesta
        print(response.text)

    def reject_capitulation(self, capitulation_id):
        capitulation = self.db.query(CapitulationModel).filter(CapitulationModel.id == capitulation_id).first()
        user = self.db.query(UserModel).filter(UserModel.rut == capitulation.user_rut).first()
        whatsapp_template = self.db.query(WhatsappTemplateModel).filter(WhatsappTemplateModel.id == 3).first()
        expense_type = self.db.query(ExpenseTypeModel).filter(ExpenseTypeModel.id == capitulation.expense_type_id).first()
        branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == capitulation.branch_office_id).first()

        phone = user.phone  # Ej: '912345678'
        full_name = user.full_name
        capitulation_id = capitulation.id
        amount_value = capitulation.amount
        capitulation_date_value = capitulation.added_date.strftime('%d-%m-%Y') if capitulation.added_date else 'N/A'
        expense_type_name = expense_type.expense_type
        branch_office_name = branch_office.branch_office
        rejection_reason = capitulation.why_was_rejected

        # URL de la API
        url = 'https://graph.facebook.com/v20.0/101066132689690/messages'

        token = os.getenv('LIBREDTE_TOKEN')

        # Cabeceras
        headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }

        phone_str = str(phone).strip()
        if not phone_str.startswith("56"):
            phone = "56" + phone_str
        else:
            phone = phone_str

        # Payload en formato JSON
        payload = {
            "messaging_product": "whatsapp",
            "to": f"{phone}",
            "type": "template",
            "template": {
                "name": whatsapp_template.title,
                "language": {"code": "es"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": full_name},
                            {"type": "text", "text": capitulation_id},
                            {"type": "text", "text": amount_value},
                            {"type": "text", "text": capitulation_date_value},
                            {"type": "text", "text": expense_type_name},
                            {"type": "text", "text": branch_office_name},
                            {"type": "text", "text": rejection_reason},
                        ]
                    }
                ]
            }
        }

        # Enviar la solicitud POST
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        # Mostrar la respuesta
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

    def dtes_data(self):
        dtes = (
            self.db.query(DteModel)
            .filter(DteModel.status_id == 5)
            .filter(DteModel.dte_type_id == 39)
            .filter(DteModel.payment_type_id == 2)
            .filter(DteModel.dte_version_id == 1)
            .filter(DteModel.period == '2025-05')
            .all()
        )

        for dte in dtes:
            try:
                print(dte.folio)

                TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

                created_dte_url = f"https://libredte.cl/api/dte/dte_emitidos/cobro/{dte.dte_type_id}/{dte.folio}/76063822?getXML=0&getDetalle=0&getDatosDte=0&getTed=0&getResolucion=0&getEmailEnviados=0&getLinks=0&getReceptor=0&getSucursal=0&getUsuario=0"

                headers = {
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json"
                }

                created_dte_response = requests.get(created_dte_url, headers=headers)
                print(created_dte_response.text)

                data = created_dte_response.json()

                if isinstance(data, dict):
                    if data.get("pagado") is not None and data.get("datos") is not None:
                        datos_dict = json.loads(data["datos"])
                        authorization_code = datos_dict["detailOutput"]["authorizationCode"]

                        print("Authorization Code:", authorization_code)

                        dte_detail = (
                            self.db.query(DteModel)
                            .filter(DteModel.status_id == dte.status_id)
                            .filter(DteModel.dte_type_id == dte.dte_type_id)
                            .filter(DteModel.dte_version_id == dte.dte_version_id)
                            .filter(DteModel.period == dte.period)
                            .first()
                        )

                        dte_detail.payment_date = data["pagado"]
                        dte_detail.comment = f'Código de autorización: {authorization_code}'
                        dte_detail.payment_comment = f'Código de autorización: {authorization_code}'
                        self.db.commit()
                    else:
                        print("Datos o pagado no disponibles para el DTE con folio", dte.folio)
                else:
                    print(f"Respuesta inesperada para DTE folio {dte.folio}: {data}")
            except Exception as e:
                print(f"❌ Error procesando DTE folio {dte.folio}: {e}")


    def dtes_data2(self):
        dtes = (
            self.db.query(DteModel)
            .filter(DteModel.status_id == 5)
            .filter(DteModel.dte_type_id == 39)
            .filter(DteModel.payment_type_id == 2)
            .filter(DteModel.dte_version_id == 1)
            .filter(DteModel.period == '2025-06')
            .all()
        )

        for dte in dtes:
            try:
                print(dte.folio)

                TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

                created_dte_url = f"https://libredte.cl/api/dte/dte_emitidos/cobro/{dte.dte_type_id}/{dte.folio}/76063822?getXML=0&getDetalle=0&getDatosDte=0&getTed=0&getResolucion=0&getEmailEnviados=0&getLinks=0&getReceptor=0&getSucursal=0&getUsuario=0"

                headers = {
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json"
                }

                created_dte_response = requests.get(created_dte_url, headers=headers)
                print(created_dte_response.text)

                data = created_dte_response.json()

                if isinstance(data, dict):
                    if data.get("pagado") is not None and data.get("datos") is not None:
                        datos_dict = json.loads(data["datos"])
                        authorization_code = datos_dict["detailOutput"]["authorizationCode"]

                        print("Authorization Code:", authorization_code)

                        dte_detail = (
                            self.db.query(DteModel)
                            .filter(DteModel.status_id == dte.status_id)
                            .filter(DteModel.dte_type_id == dte.dte_type_id)
                            .filter(DteModel.dte_version_id == dte.dte_version_id)
                            .filter(DteModel.period == dte.period)
                            .first()
                        )

                        dte_detail.payment_date = data["pagado"]
                        dte_detail.comment = f'Código de autorización: {authorization_code}'
                        dte_detail.payment_comment = f'Código de autorización: {authorization_code}'
                        self.db.commit()
                    else:
                        print("Datos o pagado no disponibles para el DTE con folio", dte.folio)
                else:
                    print(f"Respuesta inesperada para DTE folio {dte.folio}: {data}")
            except Exception as e:
                print(f"❌ Error procesando DTE folio {dte.folio}: {e}")


    def dtes_data3(self):
        dtes = (
            self.db.query(DteModel)
            .filter(DteModel.status_id == 5)
            .filter(DteModel.dte_type_id == 39)
            .filter(DteModel.payment_type_id == 2)
            .filter(DteModel.dte_version_id == 1)
            .filter(DteModel.period == '2025-04')
            .all()
        )

        for dte in dtes:
            try:
                print(dte.folio)

                TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

                created_dte_url = f"https://libredte.cl/api/dte/dte_emitidos/cobro/{dte.dte_type_id}/{dte.folio}/76063822?getXML=0&getDetalle=0&getDatosDte=0&getTed=0&getResolucion=0&getEmailEnviados=0&getLinks=0&getReceptor=0&getSucursal=0&getUsuario=0"

                headers = {
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json"
                }

                created_dte_response = requests.get(created_dte_url, headers=headers)
                print(created_dte_response.text)

                data = created_dte_response.json()

                if isinstance(data, dict):
                    if data.get("pagado") is not None and data.get("datos") is not None:
                        datos_dict = json.loads(data["datos"])
                        authorization_code = datos_dict["detailOutput"]["authorizationCode"]

                        print("Authorization Code:", authorization_code)

                        dte_detail = (
                            self.db.query(DteModel)
                            .filter(DteModel.status_id == dte.status_id)
                            .filter(DteModel.dte_type_id == dte.dte_type_id)
                            .filter(DteModel.dte_version_id == dte.dte_version_id)
                            .filter(DteModel.period == dte.period)
                            .first()
                        )

                        dte_detail.payment_date = data["pagado"]
                        dte_detail.comment = f'Código de autorización: {authorization_code}'
                        dte_detail.payment_comment = f'Código de autorización: {authorization_code}'
                        self.db.commit()
                    else:
                        print("Datos o pagado no disponibles para el DTE con folio", dte.folio)
                else:
                    print(f"Respuesta inesperada para DTE folio {dte.folio}: {data}")
            except Exception as e:
                print(f"❌ Error procesando DTE folio {dte.folio}: {e}")


    def dtes_data4(self):
        dtes = (
            self.db.query(DteModel)
            .filter(DteModel.status_id == 5)
            .filter(DteModel.dte_type_id == 39)
            .filter(DteModel.payment_type_id == 2)
            .filter(DteModel.dte_version_id == 1)
            .filter(DteModel.period == '2025-03')
            .all()
        )

        for dte in dtes:
            try:
                print(dte.folio)

                TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

                created_dte_url = f"https://libredte.cl/api/dte/dte_emitidos/cobro/{dte.dte_type_id}/{dte.folio}/76063822?getXML=0&getDetalle=0&getDatosDte=0&getTed=0&getResolucion=0&getEmailEnviados=0&getLinks=0&getReceptor=0&getSucursal=0&getUsuario=0"

                headers = {
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json"
                }

                created_dte_response = requests.get(created_dte_url, headers=headers)
                print(created_dte_response.text)

                data = created_dte_response.json()

                if isinstance(data, dict):
                    if data.get("pagado") is not None and data.get("datos") is not None:
                        datos_dict = json.loads(data["datos"])
                        authorization_code = datos_dict["detailOutput"]["authorizationCode"]

                        print("Authorization Code:", authorization_code)

                        dte_detail = (
                            self.db.query(DteModel)
                            .filter(DteModel.status_id == dte.status_id)
                            .filter(DteModel.dte_type_id == dte.dte_type_id)
                            .filter(DteModel.dte_version_id == dte.dte_version_id)
                            .filter(DteModel.period == dte.period)
                            .first()
                        )

                        dte_detail.payment_date = data["pagado"]
                        dte_detail.comment = f'Código de autorización: {authorization_code}'
                        dte_detail.payment_comment = f'Código de autorización: {authorization_code}'
                        self.db.commit()
                    else:
                        print("Datos o pagado no disponibles para el DTE con folio", dte.folio)
                else:
                    print(f"Respuesta inesperada para DTE folio {dte.folio}: {data}")
            except Exception as e:
                print(f"❌ Error procesando DTE folio {dte.folio}: {e}")

    def cron_to_resend(self):
        dtes = self.db.query(DteModel).filter(DteModel.status_id == 4).filter(DteModel.dte_type_id == 39).filter(DteModel.dte_version_id == 1).filter(DteModel.period == '2025-08').all()

        for dte in dtes:
            print(dte.folio)
            
            customer = self.db.query(CustomerModel).filter(CustomerModel.rut == dte.rut).first()
            
            self.resend(dte.id, customer.phone)

    def notify_payment(self, folio):
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


    def status_capitulation(self, rut, amount):
        user = self.db.query(UserModel).filter(UserModel.rut == rut).first()
        phone = user.phone
        whatsapp_template = self.db.query(WhatsappTemplateModel).filter(WhatsappTemplateModel.id == 5).first()

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
                                    {"type": "text", "text": amount},
                                    {"type": "text", "text": 'Pagadas'},
                                ]
                            }
                        ]
                    }
                }

        print(payload)
        response = requests.post(url, json=payload, headers=headers)

        print(response.text)