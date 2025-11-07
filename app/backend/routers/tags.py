from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin
from app.backend.classes.tag_class import TagClass
from app.backend.auth.auth_user import get_current_active_user
import os

tags = APIRouter(
    prefix="/tags",
    tags=["Tags"]
)

@tags.post("/")
def index(request: dict, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    branch_office_id = request.get("branch_office_id")
    
    # Obligar a que se haga búsqueda por sucursal
    if not branch_office_id:
        return {"message": {"data": [], "total": 0, "page": 1, "items_per_page": 10, "total_pages": 0}}
    
    page = request.get("page", 1)
    items_per_page = request.get("items_per_page", 10)
    
    data = TagClass(db).get_all(
        branch_office_id=branch_office_id,
        page=page,
        items_per_page=items_per_page
    )

    return {"message": data}

@tags.post("/create")
def create(request: dict, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = TagClass(db).store(request)
    return {"message": data}

@tags.get("/edit/{id}")
def edit(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = TagClass(db).get("id", id)
    return {"message": data}

@tags.patch("/update/{id}")
def update(id: int, request: dict, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = TagClass(db).update(id, request)
    return {"message": data}

@tags.delete("/delete/{id}")
def delete(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = TagClass(db).delete(id)
    return {"message": data}

@tags.get("/generate_pdf/{branch_office_id}")
def generate_pdf(branch_office_id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    result = TagClass(db).generate_pdf_labels(branch_office_id)
    
    if "error" in result:
        return {"message": result}
    
    # Retornar el archivo PDF
    filepath = result["filepath"]
    filename = result["filename"]
    
    return FileResponse(
        path=filepath,
        media_type='application/pdf',
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
