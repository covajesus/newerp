from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.file_class import FileClass
from app.backend.schemas import TransbankStatement, TransbankStatementList
from fastapi import UploadFile, File, HTTPException
from app.backend.classes.transbank_statement_class import TransbankStatementClass
from datetime import datetime
import uuid
from fastapi.responses import StreamingResponse
import json
import asyncio

transbank_statements = APIRouter(
    prefix="/transbank_statements",
    tags=["TransbankStatements"]
)

@transbank_statements.post("/")
def index(transbank: TransbankStatementList, db: Session = Depends(get_db)):
    data = TransbankStatementClass(db).get_all(transbank.page)

    return {"message": data}

@transbank_statements.post("/store")
def store(
    form_data: TransbankStatement = Depends(TransbankStatement.as_form),
    support: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
        file_category_name = 'transbank_statements'
        unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

        remote_path = f"{file_category_name}_{unique_filename}"

        message = FileClass(db).upload(support, remote_path)
        file_url = FileClass(db).get(remote_path)

        # Procesar el archivo sincrónicamente - esperar hasta que termine
        result = TransbankStatementClass(db).read_store_bank_statement(file_url, form_data.period)
        
        if result == 1:
            return {
                "message": "Cartola de transbank procesada exitosamente", 
                "file_url": file_url,
                "status": "completed"
            }
        else:
            raise HTTPException(status_code=500, detail="Error al procesar la cartola")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")

@transbank_statements.post("/store_with_progress")
def store_with_progress(
    form_data: TransbankStatement = Depends(TransbankStatement.as_form),
    support: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """Endpoint que usa el método con progreso interno"""
    try:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
        file_category_name = 'transbank_statements'
        unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

        remote_path = f"{file_category_name}_{unique_filename}"

        # Subir archivo
        message = FileClass(db).upload(support, remote_path)
        file_url = FileClass(db).get(remote_path)

        # Lista para capturar el progreso
        progress_log = []
        
        def capture_progress(progress, message):
            progress_log.append({"progress": progress, "message": message, "timestamp": datetime.now().isoformat()})
            print(f"Progreso: {progress}% - {message}")  # Para debugging

        # Procesar archivo con callback de progreso
        result = TransbankStatementClass(db).read_store_bank_statement_with_progress(
            file_url, 
            form_data.period,
            progress_callback=capture_progress
        )
        
        if result == 1:
            return {
                "message": "Cartola de transbank procesada exitosamente", 
                "file_url": file_url,
                "status": "completed",
                "progress_log": progress_log
            }
        else:
            raise HTTPException(status_code=500, detail="Error al procesar la cartola")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")