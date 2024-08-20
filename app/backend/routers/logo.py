from fastapi import APIRouter, Depends, Request, Response, UploadFile, File
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Employee, UpdateEmployee, SearchEmployee, UserLogin, EmployeeList, UploadSignature, UploadPicture
from app.backend.classes.employee_class import EmployeeClass
from app.backend.auth.auth_user import get_current_active_user
import base64
import os
from app.backend.classes.dropbox_class import DropboxClass
from app.backend.classes.logo_class import LogoClass
from fastapi import File, UploadFile
import dropbox

logo = APIRouter(
    prefix="/logo",
    tags=["Logo"]
)

@logo.post("/upload_logo/")
def upload_logo(support: UploadFile = File(...) , session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    dropbox_client = DropboxClass(db)

    filename = dropbox_client.upload(name=support.filename, data=support, dropbox_path='/logo/', computer_path=os.path.join(os.path.dirname(__file__)), resize=0)

    LogoClass(db).upload_logo(filename)
    return {"message": "File uploaded successfully", "file_name": filename}

@logo.delete("/delete_logo/{id}")
def delete_logo(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    dropbox_client = DropboxClass(db)
    support = LogoClass(db).delete(id)
    # Get the file from the request
    # Delete the file from Dropbox
    dropbox_client.delete("/logo/",support)

    return {"message": "File deleted successfully"}

@logo.get("/get_logos/")
def get_logos(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = LogoClass(db).get()
    return data


@logo.get("/get_logo_for_website/")
def get_logos( db: Session = Depends(get_db)):
    dropbox_client = DropboxClass(db)
    data = LogoClass(db).get()
    data.support = dropbox_client.get("/logo/",data.support )
    return data


