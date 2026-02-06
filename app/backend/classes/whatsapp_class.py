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

    def check_whatsapp_balance(self):
        """
        Valida si WhatsApp tiene crédito disponible haciendo una verificación.
        Retorna True si tiene crédito, False si no tiene (error de pago).
        """
        try:
            token = os.getenv('LIBREDTE_TOKEN')
            url = "https://graph.facebook.com/v20.0/101066132689690/messages"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Intentar enviar un mensaje de prueba usando template al número del administrador
            # Esto nos permite detectar el error de pago sin procesar DTEs reales
            test_phone = "56976357193"
            
            # Usar template simple (asumiendo que existe un template de texto simple)
            # Si no existe, se puede crear uno o usar otro template existente
            whatsapp_template = self.db.query(WhatsappTemplateModel).filter(WhatsappTemplateModel.id == 1).first()
            
            if not whatsapp_template:
                print("⚠️ No se encontró template de WhatsApp para validación")
                return False
            
            # Usar template con mensaje "Test"
            payload = {
                "messaging_product": "whatsapp",
                "to": test_phone,
                "type": "template",
                "template": {
                    "name": whatsapp_template.title,
                    "language": {"code": "es"},
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": "Test"}
                            ]
                        }
                    ]
                }
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response_data = response.json()
            
            print(f"Respuesta de validación de balance: {response_data}")
            
            # Verificar si hay error de pago
            if "error" in response_data:
                error_code = response_data.get("error", {}).get("code")
                error_message = response_data.get("error", {}).get("message", "")
                
                print(f"Error detectado - Código: {error_code}, Mensaje: {error_message}")
                
                if error_code == 131042 or "Payment required" in error_message or "(#131042)" in str(error_message):
                    print("⚠️ Error de pago detectado: WhatsApp no tiene crédito")
                    return False
            
            # Si el status code es 200, tiene crédito
            if response.status_code == 200:
                print("✅ WhatsApp tiene crédito disponible")
                return True
            
            # Si hay otro error, asumimos que no tiene crédito para ser conservadores
            print(f"⚠️ Respuesta inesperada: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"Error al validar balance de WhatsApp: {str(e)}")
            # En caso de error, asumimos que no tiene crédito para ser conservadores
            return False

    def send_notification_to_admin(self, message):
        """
        Envía un mensaje de notificación al número de administrador (976357193) usando template.
        """
        try:
            token = os.getenv('LIBREDTE_TOKEN')
            url = "https://graph.facebook.com/v20.0/101066132689690/messages"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            admin_phone = "56976357193"
            
            # Obtener template (usar template 1 como base, o el que sea apropiado)
            whatsapp_template = self.db.query(WhatsappTemplateModel).filter(WhatsappTemplateModel.id == 1).first()
            
            if not whatsapp_template:
                print("⚠️ No se encontró template de WhatsApp para notificación")
                return {
                    "status": "error",
                    "error": "Template no encontrado"
                }
            
            # Usar template con el mensaje (usando "Test" como parámetro)
            payload = {
                "messaging_product": "whatsapp",
                "to": admin_phone,
                "type": "template",
                "template": {
                    "name": whatsapp_template.title,
                    "language": {"code": "es"},
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": "Test"}
                            ]
                        }
                    ]
                }
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response_data = response.json()
            
            print(f"Notificación enviada a administrador: {response_data}")
            return {
                "status": "success" if response.status_code == 200 else "error",
                "response": response_data
            }
            
        except Exception as e:
            print(f"Error al enviar notificación a administrador: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
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

    def rejected_deposit_notification(self, deposit_data, deposit_id):
        whatsapp_template = self.db.query(WhatsappTemplateModel).filter(WhatsappTemplateModel.id == 6).first()

        """
        Envía notificación WhatsApp cuando un depósito es rechazado
        """
        try:
            # Obtener datos de la sucursal
            branch_office = self.db.query(BranchOfficeModel).filter(
                BranchOfficeModel.id == deposit_data.branch_office_id
            ).first()
            
            if not branch_office:
                print(f"No se encontró la sucursal con ID: {deposit_data.branch_office_id}")
                return
            
            # Obtener datos del supervisor principal
            user = self.db.query(UserModel).filter(
                UserModel.rut == branch_office.principal_supervisor
            ).first()
            
            if not user:
                print(f"No se encontró el supervisor principal con RUT: {branch_office.principal_supervisor}")
                return

            # Token de WhatsApp
            token = os.getenv('LIBREDTE_TOKEN')
            url = "https://graph.facebook.com/v20.0/101066132689690/messages"

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Formatear fecha de depósito
            deposit_date_formatted = 'No especificada'
            if hasattr(deposit_data, 'deposit_date') and deposit_data.deposit_date:
                try:
                    # Si viene en formato DD-MM-YYYY, mantenerlo
                    if '-' in str(deposit_data.deposit_date) and len(str(deposit_data.deposit_date).split('-')) == 3:
                        deposit_date_formatted = str(deposit_data.deposit_date)
                    else:
                        # Si viene en otro formato, intentar convertir
                        from datetime import datetime
                        date_obj = datetime.strptime(str(deposit_data.deposit_date), '%Y-%m-%d')
                        deposit_date_formatted = date_obj.strftime('%d-%m-%Y')
                except:
                    deposit_date_formatted = str(deposit_data.deposit_date)

            # Obtener motivo del rechazo
            rejection_reason = "Motivo no especificado"
            if hasattr(deposit_data, 'reject_reason_id') and deposit_data.reject_reason_id:
                if deposit_data.reject_reason_id == 1:
                    rejection_reason = "Fotografía no corresponde"
                elif deposit_data.reject_reason_id == 2:
                    rejection_reason = "Monto no cuadra"
                else:
                    rejection_reason = f"Razón ID: {deposit_data.reject_reason_id}"

            payload = {
                "messaging_product": "whatsapp",
                "to": user.phone,
                "type": "template",
                "template": {
                    "name": whatsapp_template.title,
                    "language": {"code": "es"},
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": user.full_name},
                                {"type": "text", "text": str(deposit_id)},
                                {"type": "text", "text": branch_office.branch_office},
                                {"type": "text", "text": deposit_date_formatted},
                                {"type": "text", "text": rejection_reason},
                            ]
                        }
                    ]
                }
            }

            print("Enviando notificación de depósito rechazado...")
            print(payload)
            
            response = requests.post(url, json=payload, headers=headers)
            print(f"Respuesta WhatsApp: {response.text}")
            
            return response.json()
            
        except Exception as e:
            print(f"Error al enviar notificación WhatsApp: {str(e)}")
            return None