from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import DocumentType, UpdateDocumentType, UserLogin
from app.backend.classes.document_type_class import DocumentTypeClass
from app.backend.auth.auth_user import get_current_active_user

document_types = APIRouter(
    prefix="/document_types",
    tags=["Document_Types"]
)

@document_types.get("/{document_group_id}")
def index(document_group_id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = DocumentTypeClass(db).get_all(document_group_id)

    return {"message": data}

@document_types.post("/store")
def store(document_type:DocumentType, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    document_type_inputs = document_type.dict()
    data = DocumentTypeClass(db).store(document_type_inputs)

    return {"message": data}

@document_types.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = DocumentTypeClass(db).get("id", id)

    return {"message": data}

@document_types.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = DocumentTypeClass(db).delete(id)

    return {"message": data}

@document_types.patch("/update/{id}")
def update(id: int, document_type: UpdateDocumentType, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = DocumentTypeClass(db).update(id, document_type)

    return {"message": data}