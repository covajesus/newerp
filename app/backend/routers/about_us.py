from fastapi import APIRouter, Depends, Request, Response, UploadFile, File
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import  UserLogin, UpdateAboutUs
from app.backend.classes.employee_class import EmployeeClass
from app.backend.auth.auth_user import get_current_active_user
import base64
import os
from app.backend.classes.dropbox_class import DropboxClass
from app.backend.classes.about_us_class import AboutUsClass
from fastapi import File, UploadFile
import dropbox

about_us = APIRouter(
    prefix="/about_us",
    tags=["About_us"]
)

@about_us.patch("/update_about_us/")
def update_about_us(data: UpdateAboutUs, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    AboutUsClass(db).update_about_us(data)
    return {"message": "About us updated successfully"}

@about_us.get("/get_about_us/")
def get_about_us(db: Session = Depends(get_db)):
    about_us = AboutUsClass(db).get_about_us()
    return about_us

