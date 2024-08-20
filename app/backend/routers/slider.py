from fastapi import APIRouter, Depends, Request, Response, UploadFile, File
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Employee, UpdateEmployee, SearchEmployee, UserLogin, EmployeeList, UploadSignature, UploadPicture
from app.backend.classes.employee_class import EmployeeClass
from app.backend.auth.auth_user import get_current_active_user
import base64
import os
from app.backend.classes.dropbox_class import DropboxClass
from app.backend.classes.slider_class import SliderClass
from fastapi import File, UploadFile
import dropbox

slider = APIRouter(
    prefix="/slider",
    tags=["Slider"]
)

@slider.post("/upload_image/")
def upload_image(support: UploadFile = File(...) , session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    print(support)
    dropbox_client = DropboxClass(db)

    filename = dropbox_client.upload(name=support.filename, data=support, dropbox_path='/sliders/', computer_path=os.path.join(os.path.dirname(__file__)), resize=0)

    SliderClass(db).upload_image(filename)
    return {"message": "File uploaded successfully", "file_name": filename}

@slider.delete("/delete_image/{id}")
def delete_image(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    dropbox_client = DropboxClass(db)
    support = SliderClass(db).delete(id)
    # Get the file from the request
    # Delete the file from Dropbox
    dropbox_client.delete("/sliders/",support)

    return {"message": "File deleted successfully"}

@slider.get("/get_images/")
def get_images(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = SliderClass(db).get()
    return data


@slider.get("/get_slider_for_website/")
def get_images(db: Session = Depends(get_db)):
    dropbox_client = DropboxClass(db)
    data = SliderClass(db).get()
    link = []
    for i in range(len(data)):
        data[i].support = dropbox_client.get("/sliders/",data[i].support )
        link.append(data[i].support)

    return link

