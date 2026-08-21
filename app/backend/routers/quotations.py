from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
import base64

from app.backend.auth.auth_user import get_current_active_user
from app.backend.classes.quotation_class import QuotationClass
from app.backend.db.database import get_db
from app.backend.schemas import (
    QuotationConvert,
    QuotationList,
    QuotationRenew,
    QuotationSearch,
    QuotationSend,
    StoreQuotation,
    UserLogin,
)

quotations = APIRouter(prefix="/quotations", tags=["Quotations"])

# 1x1 transparent GIF for email open tracking
_TRACKING_PIXEL_GIF = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)


@quotations.get("/email_open/{token}")
def email_open(token: str, db: Session = Depends(get_db)):
    """
    Public tracking pixel (no auth). Marks quotation email_read=1 when the mail is opened.
    """
    QuotationClass(db).mark_email_read(token)
    return Response(
        content=_TRACKING_PIXEL_GIF,
        media_type="image/gif",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )


@quotations.post("/")
def index(
    payload: QuotationList,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = QuotationClass(db).get_all(page=payload.page, items_per_page=payload.items_per_page or 10)
    return {"message": data}


@quotations.post("/search")
def search(
    payload: QuotationSearch,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = QuotationClass(db).search(
        page=payload.page,
        items_per_page=payload.items_per_page or 10,
        rut=payload.rut,
        customer=payload.customer,
        period=payload.period,
        renew_mode=payload.renew_mode,
        status_id=payload.status_id,
        branch_office_id=payload.branch_office_id,
    )
    return {"message": data}


@quotations.post("/store")
def store(
    payload: StoreQuotation,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = QuotationClass(db).store(payload)
    return {"message": data}


@quotations.get("/prefill_from_dte/{dte_id}")
def prefill_from_dte(
    dte_id: int,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = QuotationClass(db).prefill_from_dte(dte_id)
    return {"message": data}


@quotations.get("/edit/{quotation_id}")
def get_one(
    quotation_id: int,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = QuotationClass(db).get(quotation_id)
    return {"message": data}


@quotations.put("/update/{quotation_id}")
def update(
    quotation_id: int,
    payload: StoreQuotation,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = QuotationClass(db).update(quotation_id, payload)
    return {"message": data}


@quotations.delete("/annul/{quotation_id}")
def annul(
    quotation_id: int,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = QuotationClass(db).annul(quotation_id)
    return {"message": data}


@quotations.post("/send_email/{quotation_id}")
def send_email(
    quotation_id: int,
    payload: QuotationSend,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = QuotationClass(db).send_email(quotation_id, to_email=payload.email)
    return {"message": data}


@quotations.post("/send_whatsapp/{quotation_id}")
def send_whatsapp(
    quotation_id: int,
    payload: QuotationSend,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = QuotationClass(db).send_whatsapp(quotation_id, phone=payload.phone)
    return {"message": data}


@quotations.get("/pdf/{quotation_id}")
def pdf(
    quotation_id: int,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    pdf_bytes, err = QuotationClass(db).build_pdf_bytes(quotation_id)
    if not pdf_bytes:
        return {"message": {"status": "error", "message": err or "PDF error"}}
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="quotation-{quotation_id}.pdf"'},
    )


@quotations.post("/renew")
def renew(
    payload: QuotationRenew,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = QuotationClass(db).renew_period(payload.period)
    return {"message": data}


@quotations.post("/convert/{quotation_id}")
def convert(
    quotation_id: int,
    payload: QuotationConvert,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = QuotationClass(db).convert_to_dte(
        quotation_id,
        dte_type_id=payload.dte_type_id,
        rol_id=session_user.rol_id,
    )
    return {"message": data}
