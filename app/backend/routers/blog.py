from fastapi import APIRouter, Depends, Request, Response, UploadFile, File
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import  UserLogin, CreateBlog
from app.backend.classes.employee_class import EmployeeClass
from app.backend.auth.auth_user import get_current_active_user
import base64
import os
from app.backend.classes.dropbox_class import DropboxClass
from app.backend.classes.blog_class import BlogClass
from fastapi import File, UploadFile
import dropbox

blog = APIRouter(
    prefix="/blog",
    tags=["Blog"]
)

@blog.post("/store")
async def store(data: CreateBlog = Depends(CreateBlog.as_form) ,  support: UploadFile = File(...), session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    dropbox_client = DropboxClass(db)

    filename = dropbox_client.upload(name=support.filename, data=support, dropbox_path='/blog/', computer_path=os.path.join(os.path.dirname(__file__)), resize=0)

    data = BlogClass(db ).store(data,filename)
    return {"message": data}


@blog.get("/get_all")
async def get(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = BlogClass(db).get_all()
    return {"message": data}    


@blog.get("/get_all_for_website")
async def get(db: Session = Depends(get_db)):
    dropbox_client = DropboxClass(db)
    data = BlogClass(db).get_all()

    for i in range(len(data)):
        data[i].picture = dropbox_client.get("/blog/",data[i].picture )

    return {"message": data}    



# @blog.delete("/delete/{id}")
# async def delete(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
#     data = BlogClass(db).delete(id)
#     return {"message": data}