from fastapi import APIRouter, Depends, File, UploadFile
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.file_class import FileClass
from app.backend.classes.contract_class import ContractClass
from app.backend.schemas import Contract

files = APIRouter(
    prefix="/files",
    tags=["files"]
)

@files.post("/upload_contract")
def upload(form_data: Contract = Depends(Contract.as_form), support: UploadFile = File(...), db: Session = Depends(get_db)):
    remote_path = f"{support.filename}"
    contract_status = ContractClass(db).store(form_data)
    message = FileClass(db).upload(support, remote_path)
    return {"message": message}
