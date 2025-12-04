from fastapi import APIRouter, Depends
from app.backend.schemas import UserLogin, GetDte, Dte, DteList, ReceivedDteList, ImportDte, UploadDteDepositTransfer, SearchEmittedDtes
from app.backend.classes.dte_class import DteClass
from app.backend.auth.auth_user import get_current_active_user
from app.backend.classes.whatsapp_class import WhatsappClass
from app.backend.db.models import DteModel, CustomerModel
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.file_class import FileClass
from fastapi import UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse
from datetime import datetime
import pymysql
import uuid
import base64
import requests
import json

dtes = APIRouter(
    prefix="/dtes",
    tags=["Dtes"]
)

@dtes.post("/")
def index(dte: DteList, db: Session = Depends(get_db)):
    data = DteClass(db).get_all(dte.branch_office_id, dte.dte_type_id, dte.dte_version_id, dte.since, dte.until, dte.subscriber, dte.page)

    return {"message": data}

@dtes.post("/upload_deposit_transfer")
def upload_deposit_transfer(
    form_data: UploadDteDepositTransfer = Depends(UploadDteDepositTransfer.as_form),
    support: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
        file_category_name = 'dte_deposit_transfer'
        unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

        remote_path = f"{file_category_name}_{unique_filename}"

        message = FileClass(db).upload(support, remote_path)

        DteClass(db).upload_deposit_transfer(form_data, remote_path)

        return {"message": message}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")

@dtes.post("/all_with_customer")
def all_with_customer(dte: DteList, db: Session = Depends(get_db), session_user: UserLogin = Depends(get_current_active_user)):
    data = DteClass(db).get_all_with_customer(session_user.rol_id, session_user.rut, dte.folio, dte.branch_office_id, dte.rut, dte.customer, dte.period, dte.amount, dte.supervisor_id, dte.status_id, dte.dte_version_id, dte.page)

    return {"message": data}

@dtes.post("/all_with_customer_to_review")
def all_with_customer_to_review(dte: DteList, db: Session = Depends(get_db)):
    data = DteClass(db).get_all_with_customer(dte.folio, dte.branch_office_id, dte.rut, dte.customer, dte.period, dte.amount, dte.supervisor_id, dte.status_id, dte.dte_version_id, dte.page)

    return {"message": data}

@dtes.post("/import_by_rut")
def import_by_rut(dte: ImportDte, db: Session = Depends(get_db)):
    data = DteClass(db).import_by_rut(dte.rut)

    return {"message": data}

@dtes.post("/received_tributary_documents")
def received_tributary_documents(dte: ReceivedDteList, db: Session = Depends(get_db)):
    data = DteClass(db).get_received_tributary_documents(dte.folio, dte.branch_office_id, dte.rut, dte.supplier, dte.since, dte.until, dte.amount, dte.supervisor_id, dte.status_id, dte.dte_type_id, dte.dte_version_id, dte.page)

    return {"message": data}

@dtes.post("/total_quantity")
def total_quantity(user: GetDte, session_user: UserLogin = Depends(get_current_active_user)):
    user_inputs = user.dict()
    data = DteClass.get_total_quantity(user_inputs)

    return {"message": data}

@dtes.post("/total_amount")
def total_amount(user: GetDte, session_user: UserLogin = Depends(get_current_active_user)):
    user_inputs = user.dict()
    data = DteClass.get_total_amount(user_inputs)

    return {"message": data}

@dtes.get("/get_credit_notes")
def get_credit_notes(page: int = 1, items_per_page: int = 10, db: Session = Depends(get_db), session_user: UserLogin = Depends(get_current_active_user)):
    data = DteClass(db).get_credit_notes(session_user.rol_id, session_user.rut, session_user.branch_office_id, page, items_per_page)
    return data

@dtes.get("/send_to_sii/{machine_id}")
def send_to_sii(machine_id:int, db: Session = Depends(get_db)):
    DteClass(db).send_to_sii(machine_id)

    return {"message": '1'}

@dtes.get("/very_sent_to_sii")
def very_sent_to_sii(db: Session = Depends(get_db)):
    DteClass(db).very_sent_to_sii()

    return {"message": '1'}

@dtes.post("/store")
def store(dte:Dte, db: Session = Depends(get_db)):
    dte_inputs = dte.dict()
    
    data = DteClass(db).store(dte_inputs)
    
    return {"message": data}

@dtes.get("/validate_quantity_tickets/{total_machine_ticket}/{branch_office_id}/{cashier_id}/{added_date}")
def validate_quantity_tickets(total_machine_ticket:int, branch_office_id:int, cashier_id:int, added_date:str, db: Session = Depends(get_db)):
    data = DteClass(db).validate_quantity_tickets(total_machine_ticket, branch_office_id, cashier_id, added_date)
    
    return data

@dtes.delete("/delete/{folio}/{branch_office_id}/{cashier_id}/{added_date}/{single}")
def delete(folio:int, branch_office_id:int, cashier_id:int, added_date:str, single:int, db: Session = Depends(get_db)):
    data = DteClass(db).delete(folio, branch_office_id, cashier_id, added_date, single)
    
    return {"message": data}

@dtes.get("/existence/{folio}")
def existence(folio:int, db: Session = Depends(get_db)):
    data = DteClass(db).existence(folio)
    
    return {"message": data}

@dtes.get("/open_customer_billing_period/{period}")
def existence(period:str, db: Session = Depends(get_db)):
    data = DteClass(db).open_customer_billing_period(period)
    
    return {"message": data}

@dtes.get("/resend/{dte_id}/{phone}/{email}")
def resend(dte_id: int, phone: int, email: str, db: Session = Depends(get_db)):
    if phone != 0 and phone is not None and phone != "":
        data = WhatsappClass(db).resend(dte_id, phone)

    if email != "" and email is not None:
        data = DteClass(db).resend(dte_id, email)

    return {"message": data}

@dtes.get("/massive_resend")
def massive_resend(db: Session = Depends(get_db)):
    dte_data = db.query(DteModel).filter(DteModel.status_id == 4).filter(DteModel.branch_office_id == 78).filter(DteModel.dte_version_id == 1).all()

    for dte in dte_data:
        customer = db.query(CustomerModel).filter(CustomerModel.rut == dte.rut).first()

        if customer:
            if customer.phone != None and customer.phone != "":
                WhatsappClass(db).resend(dte.id, customer.phone)

    return {"message": "Listo"}

@dtes.get("/get_massive_codes")
def get_massive_codes(db: Session = Depends(get_db)):
    DteClass(db).get_massive_codes()

    return {"message": "Listo"}

@dtes.get("/refresh_import_by_rut")
def refresh_import_by_rut(db: Session = Depends(get_db)):
    DteClass(db).refresh_import_by_rut()

    return {"message": "Listo"}

@dtes.get("/cron_send")
def cron_send(db: Session = Depends(get_db)):
    print("Enviando DTEs a Whatsapp")
    WhatsappClass(db).cron_to_resend()

    return {"message": "Listo"}

@dtes.get("/dtes_data")
def dtes_data(db: Session = Depends(get_db)):
    print("Enviando DTEs a Whatsapp")
    WhatsappClass(db).dtes_data()

    return {"message": "Listo"}

@dtes.get("/dtes_data2")
def dtes_data(db: Session = Depends(get_db)):
    print("Enviando DTEs a Whatsapp")
    WhatsappClass(db).dtes_data2()

    return {"message": "Listo"}

@dtes.get("/info/{dte_type_id}/{folio}/{issuer}")
def get_dte_info(dte_type_id: int, folio: int, issuer: str = "76063822", db: Session = Depends(get_db)):
    try:
        dte_class = DteClass(db)
        result = dte_class.get_dte_data(dte_type_id, folio, issuer)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener información del DTE: {str(e)}")

async def auth_check(request: Request, user: str, password: str) -> bool:
    print(user, password)
    # Leer cabeceras HTTP
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return False
    
    try:
        basic, encoded = auth_header.split(" ")
        if basic.lower() != "basic":
            return False
        decoded = base64.b64decode(encoded).decode("utf-8")
        u, p = decoded.split(":", 1)
    except Exception:
        return False
    print(u, p)
    return u == user and p == password

@dtes.get("/dte_pay/{folio}")
async def dte_pay(folio: int, db: Session = Depends(get_db)):
    WhatsappClass(db).notify_payment(folio)

@dtes.post("/pay")
async def pay(request: Request, db: Session = Depends(get_db)):
    # 1. Verificar credenciales
    if not await auth_check(request, 'rcabezas', 'Jisparking2022'):
        raise HTTPException(status_code=401, detail="Usuario no autenticado o credenciales incorrectas")

    # 2. Recibir datos del cobro
    cobro_informado = await request.json()
    codigo = cobro_informado.get("codigo")
    if not codigo or not isinstance(codigo, str) or len(codigo.strip()) == 0:
        raise HTTPException(status_code=400, detail="Código de cobro inválido o no recibido")

    # 3. Consultar cobro en LibreDTE
    url = f"https://libredte.cl/api/pagos/cobros/info/{codigo}/76063822"
    headers = {"Authorization": f"Bearer JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error al conectar con LibreDTE: {str(e)}")

    # 4. Verificar respuesta
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Error LibreDTE: {resp.text}")

    try:
        Cobro = resp.json()
    except ValueError:
        raise HTTPException(status_code=500, detail=f"Respuesta inválida de LibreDTE: {resp.text}")

    if not Cobro.get("pagado"):
        raise HTTPException(status_code=400, detail="El cobro no está pagado")

    # 5. Procesar datos del cobro
    datos = Cobro.get("datos", {})
    authorization_code = datos.get("detailOutput", {}).get("authorizationCode")
    if not authorization_code:
        raise HTTPException(status_code=500, detail="No se encontró código de autorización en la respuesta de LibreDTE")

    # 6. Buscar y actualizar DTE
    dte_qty = db.query(DteModel).filter(
        DteModel.folio == Cobro["emitido"],
        DteModel.dte_version_id == 1
    ).count()

    if dte_qty > 0:
        dte = db.query(DteModel).filter(
            DteModel.folio == Cobro["emitido"],
            DteModel.dte_version_id == 1
        ).first()
        dte.payment_type_id = 2
        dte.payment_date = Cobro["pagado"]
        dte.comment = f"Código de autorización: {authorization_code}"
        dte.payment_comment = f"Código de autorización: {authorization_code}"
        dte.expense_type_id = 25
        dte.status_id = 5
        db.commit()

    WhatsappClass(db).notify_payment(Cobro["emitido"])

    return {"status": "success", "message": "DTE actualizado correctamente"}

@dtes.get("/dtes_data3")
def dtes_data(db: Session = Depends(get_db)):
    print("Enviando DTEs a Whatsapp")
    WhatsappClass(db).dtes_data3()

    return {"message": "Listo"}

@dtes.get("/dtes_data4")
def dtes_data(db: Session = Depends(get_db)):
    print("Enviando DTEs a Whatsapp")
    WhatsappClass(db).dtes_data4()

    return {"message": "Listo"}

@dtes.get("/old_dtes")
def old_dtes(db: Session = Depends(get_db)):
    conn = pymysql.connect(
        host='jisparking.com',
        user='jysparki_admin',
        password='Admin2024$',
        db='jysparki_jis',
        cursorclass=pymysql.cursors.DictCursor
    )

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 
                folio,
                rut,
                branch_office_id,
                period,
                status_id,
                expense_type_id,
                payment_type_id,
                payment_date,
                payment_comment,
                comment,
                dte_version_id,
                deposit_number,
                dte_type_id,
                chip_id,
                amount
            FROM dtes
            WHERE dte_version_id = 1 and DATE(created_at) >= '2025-07-01'and (status_id = 18 OR status_id = 19)
        """)
        result = cursor.fetchall()

        for row in result:
            folio = row['folio']
            branch_office_id = row['branch_office_id']
            rut = row['rut']
            period = row['period']
            status_id = row['status_id']
            expense_type_id = row['expense_type_id']
            payment_type_id = row['payment_type_id']
            payment_date = row['payment_date']
            payment_comment = row['payment_comment']
            comment = row['comment']
            dte_version_id = row['dte_version_id']
            dte_type_id = row['dte_type_id']
            cash_amount = row['amount']
            payment_number = row['deposit_number']
            
            if status_id == 18:
                status_id = 4
            else:
                status_id = 5

            chip_id = row['chip_id']

            print(folio)

            existence = db.query(DteModel).filter(
                DteModel.folio == folio,
                DteModel.rut == rut,
                DteModel.dte_version_id == dte_version_id,
                DteModel.dte_type_id == dte_type_id
            ).count()

            if existence == 1:
                dte_data = db.query(DteModel).filter(
                    DteModel.folio == folio,
                    DteModel.rut == rut,
                    DteModel.dte_version_id == dte_version_id,
                    DteModel.dte_type_id == dte_type_id
                ).first()

                if dte_data.status_id != 5:
                    dte_data.status_id = status_id
                    dte_data.period = period
                    dte_data.expense_type_id = expense_type_id
                    dte_data.payment_type_id = payment_type_id
                    dte_data.payment_date = payment_date
                    dte_data.payment_number = payment_number
                    dte_data.payment_comment = comment
                    dte_data.comment = comment
                    dte_data.chip_id = chip_id
                    dte_data.added_date='2025-07-01 00:00:00',
                    db.commit()
                else:
                    dte_data.expense_type_id = expense_type_id
                    dte_data.payment_type_id = payment_type_id
                    dte_data.expense_type_id = expense_type_id
                    dte_data.period = period
                    dte_data.payment_date = payment_date
                    dte_data.payment_number = payment_number
                    dte_data.payment_comment = comment
                    dte_data.comment = comment
                    dte_data.chip_id = chip_id
                    dte_data.added_date='2025-07-01 00:00:00',
                    db.commit()
            else:
                new_dte = DteModel(
                    folio=folio,
                    branch_office_id=branch_office_id,
                    rut=rut,
                    period=period,
                    status_id=status_id,
                    expense_type_id=expense_type_id,
                    payment_type_id=payment_type_id,
                    payment_date=payment_date,
                    cash_amount=cash_amount,
                    payment_comment=comment,
                    subtotal = (cash_amount) - (cash_amount * 0.19),
                    tax = (cash_amount * 0.19),
                    total = cash_amount,
                    dte_version_id=dte_version_id,
                    payment_number=payment_number,
                    dte_type_id=dte_type_id,
                    comment=comment,
                    chip_id=chip_id,
                    added_date='2025-07-01 00:00:00',
                )
                db.add(new_dte)
                db.commit()
                print('DTE guardado:', folio)

    conn.close()

    return {"data": result}

@dtes.get("/send_ticket_bill_assets/{period}")
def send_ticket_bill_assets(period: str, db: Session = Depends(get_db)):
    """
    Obtiene DTEs con dte_version_id=2, que tengan expense_type_id definido 
    y status_id igual a 4 o 5 para un período específico y crea asientos contables.
    Primero elimina asientos existentes de FacturaCompra para el período.
    """
    try:
        from app.backend.db.models import ExpenseTypeModel, BranchOfficeModel
        from app.backend.classes.helper_class import HelperClass
        import json
        
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
        
        # PASO 1: Eliminar asientos existentes de FacturaCompra para el período
        print(f"🗑️ Eliminando asientos de FacturaCompra existentes para período: {period}")
        
        # Buscar asientos con FacturaCompra en la glosa para el período
        search_params = {
            "cuenta": None,
            "debe": None,
            "debe_desde": None,
            "debe_hasta": None,
            "fecha_desde": f"{period}-01",
            "fecha_hasta": f"{period}-31",
            "glosa": "FacturaCompra",
            "haber": None,
            "haber_desde": None,
            "haber_hasta": None,
            "operacion": None,
            "periodo": int(period.split('-')[0])  # Solo el año
        }
        
        print(f"🔍 Parámetros de búsqueda FacturaCompra: {search_params}")
        
        # Buscar asientos existentes en LibreDTE
        response = requests.post(
            "https://libredte.cl/api/lce/lce_asientos/buscar/76063822",
            json=search_params,
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
            },
        )
        
        print(f"📡 Respuesta búsqueda FacturaCompra: {response.status_code}")
        print(f"📄 Contenido: {response.text}")
        
        # Procesar respuesta de búsqueda
        try:
            asientos = json.loads(response.text)
            if isinstance(asientos, list):
                asientos_list = asientos
            elif isinstance(asientos, dict) and 'data' in asientos:
                asientos_list = asientos['data']
            else:
                asientos_list = []
        except json.JSONDecodeError:
            asientos_list = []
        
        print(f"📊 Total de asientos FacturaCompra encontrados: {len(asientos_list)}")
        
        eliminated_entries = []
        
        # Eliminar cada asiento encontrado
        for asiento in asientos_list:
            if isinstance(asiento, dict) and "glosa" in asiento and "fecha" in asiento:
                print(f"🔍 Revisando asiento: {asiento.get('asiento', 'N/A')} - {asiento.get('glosa', 'N/A')} - {asiento.get('fecha', 'N/A')}")
                
                # Verificar criterios de eliminación para FacturaCompra
                has_factura_compra = "FacturaCompra" in asiento["glosa"]
                has_period = period in asiento["fecha"]
                
                print(f"   📋 FacturaCompra en glosa: {has_factura_compra}")
                print(f"   📅 Período {period} en fecha: {has_period}")
                
                if has_factura_compra and has_period:
                    # Verificar si el asiento tiene el campo 'asiento'
                    if 'asiento' not in asiento:
                        print(f"⚠️ Asiento no tiene campo 'asiento', saltando eliminación: {asiento}")
                        continue
                        
                    try:
                        codigo_asiento = asiento['asiento']
                        print(f"🗑️ Intentando eliminar asiento FacturaCompra: {codigo_asiento}")
                        
                        # Usar formato año/asiento/contribuyente
                        year = period.split('-')[0]
                        delete_url = f"https://libredte.cl/api/lce/lce_asientos/eliminar/{year}/{codigo_asiento}/76063822"
                        print(f"🔗 URL de eliminación: {delete_url}")
                        
                        delete_response = requests.get(
                            delete_url,
                            headers={
                                "Authorization": f"Bearer {TOKEN}",
                                "Content-Type": "application/json",
                            },
                        )
                        print(f"📡 Respuesta eliminación: {delete_response.status_code} - {delete_response.text}")
                        
                        eliminated_entries.append({
                            "codigo": codigo_asiento,
                            "glosa": asiento.get("glosa", 'N/A'),
                            "delete_status": delete_response.status_code,
                            "response": delete_response.text
                        })
                        
                        if delete_response.status_code == 200:
                            print(f"✅ Eliminado asiento FacturaCompra: {codigo_asiento}")
                        else:
                            print(f"❌ No se pudo eliminar asiento: {codigo_asiento} - Status: {delete_response.status_code}")
                            
                    except Exception as e:
                        print(f"❌ Error eliminando asiento FacturaCompra: {str(e)}")
                else:
                    print(f"⏭️ Asiento no cumple criterios para eliminación")
            else:
                print(f"⚠️ Asiento no tiene estructura válida: {asiento}")
        
        print(f"🧹 Eliminación completada. {len(eliminated_entries)} asientos procesados.")
        
        # PASO 2: Crear nuevos asientos contables
        print(f"💼 Iniciando creación de nuevos asientos FacturaCompra para período: {period}")
        
        # Filtros según los criterios especificados
        filters = [
            DteModel.dte_version_id == 2,
            DteModel.expense_type_id.isnot(None),  # Que tenga expense_type_id definido
            DteModel.status_id.in_([4, 5]),       # status_id igual a 4 o 5
            DteModel.period == period              # Período específico
        ]
        
        # Consulta para obtener los DTEs que cumplen los criterios
        dtes = db.query(DteModel).filter(*filters).all()
        
        # Procesar cada DTE en un foreach
        result = []
        successful_entries = 0
        failed_entries = 0
        
        for dte in dtes:
            try:
                # Obtener datos necesarios para el asiento contable
                expense_type = db.query(ExpenseTypeModel).filter(
                    ExpenseTypeModel.id == dte.expense_type_id
                ).first()
                
                branch_office = db.query(BranchOfficeModel).filter(
                    BranchOfficeModel.id == dte.branch_office_id
                ).first()
                
                if not expense_type or not branch_office:
                    result.append({
                        "id": dte.id,
                        "folio": dte.folio,
                        "status": "error",
                        "message": "Expense type or branch office not found"
                    })
                    failed_entries += 1
                    continue
                
                # Crear fechas y glosa
                american_date = period + '-01'
                utf8_date = HelperClass.convert_to_utf8(american_date)
                
                gloss = (
                    branch_office.branch_office
                    + "_"
                    + expense_type.accounting_account
                    + "_"
                    + utf8_date
                    + "_FacturaCompra_"
                    + str(dte.id)
                    + "_"
                    + str(dte.folio)
                )
                amount = dte.total
                
                # Crear estructura del asiento según el tipo de DTE
                if dte.dte_type_id == 34:  # Factura exenta
                    data = {
                        "fecha": american_date,
                        "glosa": gloss,
                        "detalle": {
                            "debe": {
                                expense_type.accounting_account.strip(): amount,
                            },
                            "haber": {
                                "111000102": amount,
                            },
                        },
                        "operacion": "E",
                        "documentos": {
                            "recibidos": [
                                {
                                    "dte": dte.dte_type_id,
                                    "folio": dte.folio,
                                }
                            ]
                        },
                    }
                else:  # Para DTEs con IVA (33, 39, etc.)
                    data = {
                        "fecha": american_date,
                        "glosa": gloss,
                        "detalle": {
                            "debe": {
                                expense_type.accounting_account.strip(): round(amount / 1.19),
                                "111000122": round(amount - (amount / 1.19)),
                            },
                            "haber": {
                                "111000102": amount,
                            },
                        },
                        "operacion": "E",
                        "documentos": {
                            "recibidos": [
                                {
                                    "dte": dte.dte_type_id,
                                    "folio": dte.folio,
                                }
                            ]
                        },
                    }
                
                # Enviar asiento a LibreDTE
                url = f"https://libredte.cl/api/lce/lce_asientos/crear/76063822"
                
                response = requests.post(
                    url,
                    json=data,
                    headers={
                        "Authorization": f"Bearer {TOKEN}",
                        "Content-Type": "application/json",
                    },
                )
                
                # Procesar respuesta
                dte_result = {
                    "id": dte.id,
                    "folio": dte.folio,
                    "rut": dte.rut,
                    "branch_office_id": dte.branch_office_id,
                    "expense_type_id": dte.expense_type_id,
                    "status_id": dte.status_id,
                    "period": dte.period,
                    "total": dte.total,
                    "dte_version_id": dte.dte_version_id,
                    "dte_type_id": dte.dte_type_id,
                    "added_date": dte.added_date.strftime('%Y-%m-%d %H:%M:%S') if dte.added_date else None,
                    "payment_date": dte.payment_date.strftime('%Y-%m-%d') if dte.payment_date else None,
                    "glosa": gloss,
                    "libredte_response_status": response.status_code,
                    "libredte_response": response.text
                }
                
                if response.status_code == 200:
                    dte_result["accounting_status"] = "success"
                    dte_result["message"] = "Accounting entry created successfully"
                    successful_entries += 1
                else:
                    dte_result["accounting_status"] = "failed"
                    dte_result["message"] = "Accounting entry creation failed"
                    failed_entries += 1
                
                result.append(dte_result)
                
            except Exception as e:
                result.append({
                    "id": dte.id,
                    "folio": dte.folio,
                    "status": "error",
                    "message": f"Error processing DTE: {str(e)}"
                })
                failed_entries += 1
        
        return {
            "status": "success",
            "period": period,
            "eliminated_factura_compra": len(eliminated_entries),
            "total_dtes": len(result),
            "successful_entries": successful_entries,
            "failed_entries": failed_entries,
            "message": f"Eliminados {len(eliminated_entries)} asientos FacturaCompra. Procesados {len(result)} DTEs para el período {period}. {successful_entries} exitosos, {failed_entries} fallidos.",
            "elimination_details": eliminated_entries,
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar DTEs: {str(e)}")

@dtes.get("/total_dtes_to_be_sent/{branch_office_id}/{dte_type_id}")
def total_dtes_to_be_sent(branch_office_id: int, dte_type_id: int, db: Session = Depends(get_db)):
    """
    Endpoint para obtener la cantidad total de DTEs que deben ser enviados masivamente por sucursal y tipo
    
    Parámetros:
    - branch_office_id: ID de la sucursal (si es 0, cuenta todas las sucursales)
    - dte_type_id: ID del tipo de DTE (si es 0, cuenta todos los tipos)
    """
    try:
        dte_class = DteClass(db)
        quantity = dte_class.total_dtes_to_be_sent(branch_office_id, dte_type_id)

        # Obtener período actual para el response
        current_period = datetime.now().strftime('%Y-%m')
        
        return {
            "status": "success", 
            "quantity": quantity,
            "branch_office_id": branch_office_id,
            "dte_type_id": dte_type_id,
            "period": current_period,
            "message": f"Total DTEs to be sent for branch {branch_office_id} and type {dte_type_id}: {quantity}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener DTEs para envío masivo: {str(e)}")

@dtes.get("/decrease_dtes_to_be_sent")
def decrease_dtes_to_be_sent(db: Session = Depends(get_db)):
    """
    Endpoint para decrementar manualmente la cantidad de DTEs pendientes (para testing)
    """
    try:
        dte_class = DteClass(db)
        remaining = dte_class.decrease_dtes_to_be_sent()
        
        return {
            "status": "success", 
            "remaining_quantity": remaining,
            "message": f"DTEs restantes: {remaining}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al decrementar DTEs pendientes: {str(e)}")

@dtes.get("/send_massive_dtes")
def send_massive_dtes(db: Session = Depends(get_db)):
    """
    Endpoint para enviar WhatsApp masivamente a DTEs del período actual con status_id = 2
    """
    try:
        dte_class = DteClass(db)
        result = dte_class.send_massive_dtes()
        
        return {
            "message": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en envío masivo de WhatsApp: {str(e)}")

@dtes.get("/send_massive_dtes_stream/{branch_office_id}/{dte_type_id}")
def send_massive_dtes_stream(branch_office_id: int, dte_type_id: int, db: Session = Depends(get_db)):
    """
    Endpoint para enviar WhatsApp masivamente con streaming de respuestas en tiempo real
    
    Parámetros:
    - branch_office_id: ID de la sucursal (si es 0, procesa todas las sucursales)
    - dte_type_id: ID del tipo de DTE (si es 0, procesa todos los tipos)
    
    Comportamiento:
    - branch_office_id = 0: Envía DTEs de todas las sucursales
    - branch_office_id > 0: Envía DTEs solo de la sucursal específica
    - dte_type_id = 0: Procesa todos los tipos de DTE
    - dte_type_id > 0: Procesa solo el tipo de DTE específico
    """
    def generate_dte_stream():
        try:
            dte_class = DteClass(db)
            
            # Obtener el período actual
            current_period = datetime.now().strftime('%Y-%m')
            
            # Construir filtro base - SOLO status_id = 2 (no procesados)
            base_filter = [
                DteModel.period == current_period,
                DteModel.status_id == 2,
                DteModel.dte_version_id == 1
            ]
            
            # Si branch_office_id es 0, procesar todas las sucursales
            if branch_office_id != 0:
                base_filter.append(DteModel.branch_office_id == branch_office_id)

            # Si dte_type_id es mayor que 0, filtrar por tipo de DTE
            if dte_type_id > 0:
                base_filter.append(DteModel.dte_type_id == dte_type_id)
            
            dtes = db.query(DteModel).filter(*base_filter).all()
            
            # Enviar información inicial
            branch_info = f" de sucursal {branch_office_id}" if branch_office_id != 0 else " de todas las sucursales"
            dte_type_info = f" de tipo {dte_type_id}" if dte_type_id > 0 else " de todos los tipos"
            initial_data = {
                "type": "init",
                "period": current_period,
                "total_dtes": len(dtes),
                "branch_office_id": branch_office_id,
                "dte_type_id": dte_type_id,
                "message": f"Iniciando envío masivo para {len(dtes)} DTEs{branch_info}{dte_type_info} del período {current_period}"
            }
            yield f"data: {json.dumps(initial_data)}\n\n"
            
            if not dtes:
                branch_scope = f" en sucursal {branch_office_id}" if branch_office_id != 0 else " en todas las sucursales"
                dte_type_scope = f" de tipo {dte_type_id}" if dte_type_id > 0 else " de todos los tipos"
                no_data = {
                    "type": "complete",
                    "total_dtes": 0,
                    "successful_sends": 0,
                    "failed_sends": 0,
                    "branch_office_id": branch_office_id,
                    "dte_type_id": dte_type_id,
                    "message": f"No hay DTEs para procesar{branch_scope}{dte_type_scope}"
                }
                yield f"data: {json.dumps(no_data)}\n\n"
                return
            
            # Procesar DTEs uno por uno usando el generador
            for progress_data in dte_class.send_massive_dtes_streaming(branch_office_id, dte_type_id):
                yield f"data: {json.dumps(progress_data)}\n\n"
            
        except Exception as e:
            error_data = {
                "type": "error",
                "message": f"Error en envío masivo: {str(e)}"
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_dte_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )