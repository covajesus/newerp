from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from app.backend.db.database import get_db
from app.backend.classes.sinister_class import SinisterClass
from app.backend.classes.file_class import FileClass
from app.backend.schemas import SinisterList, Sinister, SinisterReview
from sqlalchemy.orm import Session
from datetime import datetime
import base64
import json
import uuid

sinisters = APIRouter(
    prefix="/sinisters",
    tags=["Sinisters"]
)

@sinisters.post("/")
def index(sinister: SinisterList, db: Session = Depends(get_db)):
    sinister_data = SinisterClass(db).get_all(sinister.branch_office_id, sinister.page)

    return {"message": sinister_data}

@sinisters.post("/store")
def store(
    form_data: Sinister = Depends(Sinister.as_form),
    support: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
        file_category_name = 'sinister'
        unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

        remote_path = f"{file_category_name}_{unique_filename}"
        message = FileClass(db).upload(support, remote_path)
        SinisterClass(db).store(form_data, remote_path)

        return {"message": message}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")
    
@sinisters.delete("/delete/{id}")
def delete(id:int, db: Session = Depends(get_db)):
    sinister_data = SinisterClass(db).get(id)

    sinister_data = json.loads(sinister_data)

    file_name = sinister_data["sinister_data"]["support"]

    remote_path = f"{file_name}"

    message = FileClass(db).delete(remote_path)

    if message == "success":
        SinisterClass(db).delete(id)

    return {"message": message}

@sinisters.get("/download/{id}")
def download(id: int, db: Session = Depends(get_db)):
    sinister_data = SinisterClass(db).get(id)

    sinister_data = json.loads(sinister_data)
    file_name = sinister_data["sinister_data"]["support"]

    remote_path = f"{file_name}"

    file_contents = FileClass(db).download(remote_path)

    encoded_file = base64.b64encode(file_contents).decode('utf-8')

    return {
        "file_name": file_name,
        "file_data": encoded_file
    }
    
@sinisters.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    try:
        sinister_data = SinisterClass(db).get(id)

        if not sinister_data:
            raise HTTPException(status_code=404, detail="Siniestro no encontrada")

        return {"message": sinister_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el iva: {str(e)}")

@sinisters.get("/sinister_review/{id}/{sinister_step_type_id}")
def edit(id: int, sinister_step_type_id: int, db: Session = Depends(get_db)):
    try:
        sinister_data = SinisterClass(db).get_sinister_review(id, sinister_step_type_id)
        
        if not sinister_data:
            raise HTTPException(status_code=404, detail="Siniestro no encontrada")

        return {"message": sinister_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el iva: {str(e)}")
    
@sinisters.get("/support/{id}")
def support(id: int, db: Session = Depends(get_db)):

    sinister = SinisterClass(db).get(id)

    sinister_data = json.loads(sinister)
    remote_path = sinister_data["sinister_data"]["support"]

    file = FileClass(db).get(remote_path)

    return {"message": file}

@sinisters.get("/review_support/{id}/{sinister_step_type_id}")
def review_support(id: int, sinister_step_type_id: int, db: Session = Depends(get_db)):

    sinister = SinisterClass(db).get_sinister_review(id, sinister_step_type_id)

    sinister_data = json.loads(sinister)
    remote_path = sinister_data["sinister_data"]["support"]

    file = FileClass(db).get(remote_path)

    return {"message": file}

@sinisters.post("/store_review")
def store_review(
    form_data: SinisterReview = Depends(SinisterReview.as_form),
    support: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        if support != None:
            timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            unique_id = uuid.uuid4().hex[:8]
            file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
            file_category_name = 'sinister'
            unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

            remote_path = f"{file_category_name}_{unique_filename}"
            message = FileClass(db).upload(support, remote_path)
        
            SinisterClass(db).store_review(form_data, remote_path)
        else:
            message = SinisterClass(db).update(form_data.sinister_id, form_data.answer_step_1, '', form_data.sinister_version_id)

        return {"message": message}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")