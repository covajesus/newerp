from fastapi import APIRouter, Depends, Request, Response, UploadFile, File
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import  UserLogin, CreateFrecuentQuestion
from app.backend.classes.employee_class import EmployeeClass
from app.backend.auth.auth_user import get_current_active_user
import base64
import os

from app.backend.classes.frecuent_question_class import FrecuentQuestionClass
from fastapi import File, UploadFile
import dropbox

frecuent_questions = APIRouter(
    prefix="/frecuent_questions",
    tags=["Frecuent Questions"]
)

@frecuent_questions.post("/store")
async def store(data: CreateFrecuentQuestion ,  session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = FrecuentQuestionClass(db ).store(data)
    return {"message": data}


@frecuent_questions.get("/get_all")
async def get(db: Session = Depends(get_db)):
    data = FrecuentQuestionClass(db).get_all()
    return {"message": data}    





# @frecuent_questions.delete("/delete/{id}")
# async def delete(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
#     data = FrecuentQuestionClass(db).delete(id)
#     return {"message": data}