import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Form, HTTPException
from app.backend.auth.auth_user import get_current_active_user
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.file_class import FileClass
from app.backend.classes.intership_class import IntershipClass
from fastapi import UploadFile, File
from datetime import datetime
import uuid
from app.backend.schemas import UserLogin, IntershipList
from fastapi import APIRouter, Depends, Form, UploadFile

interships = APIRouter(
    prefix="/interships",
    tags=["Interships"]
)

@interships.post("/")
def index(internship: IntershipList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = IntershipClass(db).get_all(internship.branch_office_id, internship.intern, session_user.rol_id, session_user.rut, internship.page)

    return {"message": data}

@interships.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    try:
        intership_data = IntershipClass(db).get(id)
        
        if not intership_data:
            raise HTTPException(status_code=404, detail="Pasantía no encontrada")

        return {"message": intership_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener la pasantía: {str(e)}")

@interships.get("/questions_answers/{intership_id}/{question_id}")
def questions_answers(intership_id: int, question_id: int, db: Session = Depends(get_db)):
    message = IntershipClass(db).get_answers(intership_id, question_id)

    return message

@interships.get("/support/{support}")
def get_support(support: str, db: Session = Depends(get_db)):
    remote_path = support

    file = FileClass(db).get(remote_path)

    return {"message": file}

@interships.delete("/delete/{id}")
def delete(id: int, db: Session = Depends(get_db)):
    IntershipClass(db).delete(id)

    for question_id in range(1, 28):
        intership_data = IntershipClass(db).get_answers(id, question_id)
    
        if intership_data["image"]:
            remote_path = intership_data["image"]
            message = FileClass(db).delete(remote_path)

            if message == "success":
                print(f"Archivo asociado a la pregunta {question_id} eliminado correctamente.")

    return {"message": "success"}

@interships.post("/store")
def store(
    branch_office_id: int = Form(...),
    questions: List[str] = Form(...),
    answers: List[str] = Form(...),
    observations: List[str] = Form(None),  # ahora opcional
    files: List[UploadFile] = File(None),  # ahora opcional
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    internship_id = IntershipClass(db).store(branch_office_id, session_user.rut)

    for i in range(len(questions)):
        # Manejo del archivo
        support = files[i] if files and i < len(files) else None
        remote_path = None

        if support and support.filename != "empty-file.jpg":
            timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            unique_id = uuid.uuid4().hex[:8]
            file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
            file_category_name = 'intership'
            unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"
            remote_path = f"{file_category_name}_{unique_filename}"

            FileClass(db).upload(support, remote_path)

        # Manejo de observación
        observation_value = (
            observations[i] if observations and i < len(observations) and observations[i] else None
        )

        # Guardar respuesta
        IntershipClass(db).store_answer(
            internship_id,
            questions[i],
            answers[i],
            observation_value,
            remote_path
        )

    return {"message": "Pasantía creada con éxito", "internship_id": internship_id}