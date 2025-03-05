from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from app.backend.classes.authentication_class import AuthenticationClass
from sqlalchemy.orm import Session

biller_data = APIRouter(
    prefix="/biller_data",
    tags=["BillerData"]
)

@biller_data.get("/get_token")
def get_token(db: Session = Depends(get_db)):
    authentication_class = AuthenticationClass(db).get_token()

    return {"message": authentication_class}

@biller_data.get("/check_token")
def check_token(db: Session = Depends(get_db)):
    authentication_class = AuthenticationClass(db).check_token()

    return {"message": authentication_class}

