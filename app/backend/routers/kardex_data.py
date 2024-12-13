from fastapi import APIRouter, Depends, File, UploadFile
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import KardexDatum, UserLogin
from app.backend.classes.kardex_datum_class import KardexDatumClass
from app.backend.classes.document_type_class import DocumentTypeClass
from app.backend.auth.auth_user import get_current_active_user
import os
from app.backend.classes.dropbox_class import DropboxClass

kardex_data = APIRouter(
    prefix="/kardex_data",
    tags=["Kardex_Data"]
)

@kardex_data.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = KardexDatumClass(db).get_all()

    return {"message": data}

@kardex_data.post("/store")
def store(form_data: KardexDatum = Depends(KardexDatum.as_form), support: UploadFile = File(...), session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    document_type = DocumentTypeClass(db).get("id", form_data.document_type_id)
    
    dropbox_client = DropboxClass(db)

    filename = dropbox_client.upload(name=str(form_data.rut), description=str(document_type.document_type), data=support,
                                 dropbox_path='/employee_documents/', computer_path=os.path.join(os.path.dirname(__file__)))

    data = KardexDatumClass(db).store(form_data, filename)

    return {"message": data}

@kardex_data.get("/edit/{rut}")
def edit(rut:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = KardexDatumClass(db).get("rut", rut, 2)

    return {"message": data}

@kardex_data.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    kardex_datum = KardexDatumClass(db).get("id", id, 1)

    response = KardexDatumClass(db).delete(id)

    if response == 1:
        if kardex_datum['support'] != None or kardex_datum['support'] != '':
            response = DropboxClass(db).delete('/employee_documents/', kardex_datum['support'])

        if response == 1:
            data = 1
        else:
            data = response
    else:
        data = 0

@kardex_data.get("/download/{id}")
def download(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = KardexDatumClass(db).download(id)

    return {"message": data}