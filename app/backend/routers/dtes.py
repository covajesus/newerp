from fastapi import APIRouter, Depends
from app.backend.schemas import UserLogin, GetDte, Dte, DteList, ReceivedDteList, ImportDte, UploadDteDepositTransfer
from app.backend.classes.dte_class import DteClass
from app.backend.auth.auth_user import get_current_active_user
from app.backend.classes.whatsapp_class import WhatsappClass
from app.backend.db.models import DteModel, CustomerModel
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.file_class import FileClass
from fastapi import UploadFile, File, HTTPException
from datetime import datetime
import uuid

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
def all_with_customer(dte: DteList, db: Session = Depends(get_db)):
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
