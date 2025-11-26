from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import ReceivedTributaryDocumentList, ChangeStatusReceivedTributaryDocument, ReceivedTributaryDocumentToPay
from app.backend.classes.received_tributary_document_class import ReceivedTributaryDocumentClass
from app.backend.db.models import DteModel
import pymysql

received_tributary_documents = APIRouter(
    prefix="/received_tributary_documents",
    tags=["ReceivedTributaryDocuments"]
)

@received_tributary_documents.post("/")
def index(received_tributary_document_inputs:ReceivedTributaryDocumentList, db: Session = Depends(get_db)):
    data = ReceivedTributaryDocumentClass(db).get_all(received_tributary_document_inputs.page)

    return {"message": data}

@received_tributary_documents.post("/pay")
def pay(received_tributary_document_inputs:ReceivedTributaryDocumentToPay, db: Session = Depends(get_db)):
    data = ReceivedTributaryDocumentClass(db).pay(received_tributary_document_inputs)

    return {"message": data}

@received_tributary_documents.post("/all_supplier_bills/{rut}")
def all_supplier_bills(rut:str, db: Session = Depends(get_db)):
    data = ReceivedTributaryDocumentClass(db).get_all_supplier_bills(rut)

    return {"message": data}

@received_tributary_documents.get("/refresh")
def refresh(db: Session = Depends(get_db)):
    data = ReceivedTributaryDocumentClass(db).refresh()

    return {"message": data}

@received_tributary_documents.post("/change_status")
def change_status(received_tributary_document_inputs:ChangeStatusReceivedTributaryDocument, db: Session = Depends(get_db)):
    data = ReceivedTributaryDocumentClass(db).change_status(received_tributary_document_inputs)

    return {"message": data}

@received_tributary_documents.get("/edit/{id}")
def edit(id:int, db: Session = Depends(get_db)):
    data = ReceivedTributaryDocumentClass(db).get(id)

    return {"message": data}

@received_tributary_documents.get("/download/{id}")
def download(id:int, db: Session = Depends(get_db)):
    data = ReceivedTributaryDocumentClass(db).download(id)

    return {"message": data}

@received_tributary_documents.get("/pay_totals")
def pay_totals(db: Session = Depends(get_db)):
    data = ReceivedTributaryDocumentClass(db).getTotalPerSupplier()

    return {"message": data}

@received_tributary_documents.get("/old_dtes")
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
                created_at,
                amount
            FROM dtes
            WHERE dte_version_id = 2 and DATE(created_at) >= '2025-05-01'and (status_id = 18 OR status_id = 19)
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
            created_at = row['created_at']
            
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
                    dte_data.branch_office_id = branch_office_id
                    dte_data.status_id = status_id
                    dte_data.period = period
                    dte_data.expense_type_id = expense_type_id
                    dte_data.payment_type_id = payment_type_id
                    dte_data.payment_date = payment_date
                    dte_data.payment_number = payment_number
                    dte_data.payment_comment = payment_comment
                    dte_data.comment = comment
                    dte_data.chip_id = chip_id
                    dte_data.added_date= created_at
                    db.commit()
                else:
                    dte_data.branch_office_id = branch_office_id
                    dte_data.expense_type_id = expense_type_id
                    dte_data.payment_type_id = payment_type_id
                    dte_data.expense_type_id = expense_type_id
                    dte_data.period = period
                    dte_data.payment_date = payment_date
                    dte_data.payment_number = payment_number
                    dte_data.payment_comment = payment_comment
                    dte_data.comment = comment
                    dte_data.chip_id = chip_id
                    dte_data.added_date=created_at
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
                    payment_comment=payment_comment,
                    subtotal = (cash_amount) - (cash_amount * 0.19),
                    tax = (cash_amount * 0.19),
                    total = cash_amount,
                    dte_version_id=dte_version_id,
                    payment_number=payment_number,
                    dte_type_id=dte_type_id,
                    comment=comment,
                    chip_id=chip_id,
                    added_date=created_at
                )
                db.add(new_dte)
                db.commit()
                print('DTE guardado:', folio)

    conn.close()

    return {"data": result}
