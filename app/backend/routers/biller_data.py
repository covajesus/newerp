from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from app.backend.classes.customer_ticket_class import CustomerTicketClass
from sqlalchemy.orm import Session

biller_data = APIRouter(
    prefix="/biller_data",
    tags=["BillerData"]
)

@biller_data.get("/get_token")
def get_token(db: Session = Depends(get_db)):
    data = CustomerTicketClass(db).get_token()
    return {"message": data}

@biller_data.get("/check_token")
def check_token(db: Session = Depends(get_db)):
    data = CustomerTicketClass(db).check_token()
    return {"message": data}
