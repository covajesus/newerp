from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.backend.db.database import get_db
from app.backend.schemas import  UserLogin, UpdateContact
from app.backend.classes.employee_class import EmployeeClass
from app.backend.auth.auth_user import get_current_active_user
import base64
import os
from app.backend.classes.dropbox_class import DropboxClass
from app.backend.classes.contact_class import Contactclass
from app.backend.classes.helper_class import HelperClass

contacts = APIRouter(
    prefix="/contacts",
    tags=["Contacts"]
)

@contacts.post("/store") 
def send_email(request: Request):
    print(222)
    return {"message": "email sent successfully"}

@contacts.patch("/update_contact/")
def update_contact(data: UpdateContact, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    Contactclass(db).update_contact(data)
    return {"message": "contact updated successfully"}

@contacts.get("/get_contact/")
def get_contact(db: Session = Depends(get_db)):
    contact = Contactclass(db).get_contact()
    return contact

