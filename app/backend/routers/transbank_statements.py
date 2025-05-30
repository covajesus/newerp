from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.file_class import FileClass
from app.backend.schemas import TransbankStatement, TransbankStatementList
from fastapi import UploadFile, File, HTTPException
from app.backend.classes.transbank_statement_class import TransbankStatementClass
from datetime import datetime
import uuid

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

        TransbankStatementClass(db).read_store_bank_statement(file_url, form_data.period)

        return {"message": "Cartola de transbank cargada exitosamente", "file_url": file_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")