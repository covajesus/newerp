# This file contains the API routes for managing news

from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import New, UserLogin
from app.backend.classes.new_class import NewClass
from app.backend.classes.dropbox_class import DropboxClass
from app.backend.auth.auth_user import get_current_active_user
import os

# Create a router for managing news
news = APIRouter(
    prefix="/news",
    tags=["News"]
)

# Get all news data
@news.get("/")
def index(user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = NewClass(db).get_all()

    return {"message": data}

# Upload the picture and store the new data
@news.post("/store")
async def store(form_data: New = Depends(New), user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    dropbox_client = DropboxClass(db)

    filename = dropbox_client.upload(name='nueva', description='noticia', data=form_data.picture,
                                 dropbox_path='/news/', computer_path=os.path.join(os.path.dirname(__file__)))

    data = NewClass(db).store(form_data, filename)

    return {"message": data}

# Get the news data for editing
@news.get("/edit/{id}")
def edit(id:int, user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = NewClass(db).get("id", id)

    return {"message": data}

# Delete the news and associated picture
@news.delete("/delete/{id}")
def delete(id:int, user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    new = NewClass(db).get("id", id)

    response = NewClass(db).delete(id)

    if response == 1:
        response = DropboxClass(db).delete('/news/', new.picture)

        if response == 1:
            data = 1
        else:
            data = response
    else:
        data = 0
    
    return {"message": data}