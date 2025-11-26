from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from app.backend.classes.file_class import FileClass
from app.backend.classes.remuneration_class import RemunerationClass
from fastapi import UploadFile, File, HTTPException
from datetime import datetime
from sqlalchemy.orm import Session
import uuid

remuneration = APIRouter(
    prefix="/remunerations",
    tags=["Remunerations"]
)

@remuneration.post("/store")
def store(
    support: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
        file_category_name = 'remuneration'
        unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

        remote_path = f"{file_category_name}_{unique_filename}"

        message = FileClass(db).upload(support, remote_path)

        file_url = FileClass(db).get(remote_path)

        if file_extension == "xlsx":
            excel_data = RemunerationClass(db).read_store_massive_accountability(file_url)
        else:
            raise HTTPException(status_code=400, detail="Formato no compatible")

        return {"message": message, "file_url": file_url, "data": excel_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")
