from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.backend.db.database import get_db
from app.backend.classes.delivery_address_tag_class import DeliveryAddressTagClass
from app.backend.auth.auth_user import get_current_active_user
from app.backend.schemas import UserLogin

delivery_address_tags = APIRouter(
    prefix="/delivery_address_tags",
    tags=["DeliveryAddressTags"],
)


@delivery_address_tags.get("/")
def index(
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    data = DeliveryAddressTagClass(db).get_all_with_names()
    return {"message": data}


@delivery_address_tags.get("/pdf/{tag_id}")
def download_tag_pdf(
    tag_id: int,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    svc = DeliveryAddressTagClass(db)
    if svc.get_one_with_names(tag_id) is None:
        raise HTTPException(status_code=404, detail="Etiqueta no encontrada")
    pdf_bytes = svc.generate_pdf_bytes(tag_id)
    if not pdf_bytes:
        raise HTTPException(
            status_code=400,
            detail="Faltan datos obligatorios para la etiqueta (supervisor o dirección).",
        )
    filename = f"etiqueta_envio_{tag_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
