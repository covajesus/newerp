import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Form, HTTPException
from app.backend.auth.auth_user import get_current_active_user
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.file_class import FileClass
from app.backend.classes.employee_intership_class import EmployeeIntershipClass
from fastapi import UploadFile, File
from datetime import datetime
import uuid
from app.backend.schemas import UserLogin, IntershipList
from fastapi import APIRouter, Depends, Form, UploadFile

employee_interships = APIRouter(
    prefix="/employee_interships",
    tags=["EmployeeInterships"]
)

@employee_interships.post("/")
def index(internship: IntershipList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EmployeeIntershipClass(db).get_all(internship.branch_office_id, internship.intern, session_user.rol_id, session_user.rut, internship.page)

    return {"message": data}

@employee_interships.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    try:
        intership_data = EmployeeIntershipClass(db).get(id)
        
        if not intership_data:
            raise HTTPException(status_code=404, detail="Pasantía no encontrada")

        return {"message": intership_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener la pasantía: {str(e)}")

@employee_interships.get("/questions_answers/{intership_id}/{question_id}")
def questions_answers(intership_id: int, question_id: int, db: Session = Depends(get_db)):
    message = EmployeeIntershipClass(db).get_answers(intership_id, question_id)

    return message

@employee_interships.get("/support/{support}")
def get_support(support: str, db: Session = Depends(get_db)):
    remote_path = support

    file = FileClass(db).get(remote_path)

    return {"message": file}

@employee_interships.delete("/delete/{id}")
def delete(id: int, db: Session = Depends(get_db)):
    EmployeeIntershipClass(db).delete(id)

    EmployeeIntershipClass(db).delete_employee_intership_answers(id)

    return {"message": "success"}

@employee_interships.post("/store")
def store(
    branch_office_id: int = Form(...),
    questions: List[str] = Form(...),
    answers: List[str] = Form(...),
    observation: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    remote_path = None
    if file and file.filename:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
        file_category_name = 'intership'
        unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"
        remote_path = f"{file_category_name}_{unique_filename}"

        FileClass(db).upload(file, remote_path)

        internship_id = EmployeeIntershipClass(db).store(branch_office_id, session_user.rut, observation, remote_path)

    for i in range(len(questions)):
        EmployeeIntershipClass(db).store_answer(
            internship_id,
            questions[i],
            answers[i]
        )

    return {"message": "Pasantía creada con éxito", "internship_id": internship_id}
