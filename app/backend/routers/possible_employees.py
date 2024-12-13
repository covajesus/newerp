from fastapi import APIRouter, Depends, Request, Response, UploadFile, File
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import  UserLogin, CreatePossibleEmployee
from app.backend.classes.employee_class import EmployeeClass
from app.backend.auth.auth_user import get_current_active_user
from app.backend.classes.region_class import RegionClass
from app.backend.classes.commune_class import CommuneClass
from app.backend.classes.helper_class import HelperClass
import base64
import os
from app.backend.classes.dropbox_class import DropboxClass
from app.backend.classes.possible_employee_class import PossibleEmployeeClass
from fastapi import File, UploadFile
import dropbox

possible_employees = APIRouter(
    prefix="/possible_employees",
    tags=["Possible Employees"]
)
    
@possible_employees.post("/store")
async def store(data: CreatePossibleEmployee = Depends(CreatePossibleEmployee.as_form), support: UploadFile = File(...), db: Session = Depends(get_db)):
    data = data.dict()
    
    dropbox_client = DropboxClass(db)

    filename = dropbox_client.upload(name=support.filename, data=support, dropbox_path='/possible_employees_cv/', computer_path=os.path.join(os.path.dirname(__file__)), resize=0)

    file = dropbox_client.get('/possible_employees_cv/', filename)

    region = RegionClass(db).get("id", data['region'])

    data['region'] = region.region

    commune = CommuneClass(db).get("id", data['commune'])

    data['commune'] = commune.commune

    HelperClass().send_email_with_attachment(data, file)

    return "1"

@possible_employees.get("/get_all")
async def get(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PossibleEmployeeClass(db).get_all()
    return {"message": data}    


@possible_employees.get("/get_all_for_website")
async def get(db: Session = Depends(get_db)):
    dropbox_client = DropboxClass(db)
    data = PossibleEmployeeClass(db).get_all()

    for i in range(len(data)):
        data[i].picture = dropbox_client.get("/possible_employees_cv/",data[i].picture )

    return {"message": data}    



# @possible_employees.delete("/delete/{id}")
# async def delete(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
#     data = (db).delete(id)
#     return {"message": data}