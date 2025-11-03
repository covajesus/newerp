from fastapi import APIRouter, Depends, Query
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin
from app.backend.classes.branch_office_transbank_class import BranchOfficeTransbankClass
from app.backend.auth.auth_user import get_current_active_user
from typing import Optional

branch_office_transbank = APIRouter(
    prefix="/branch_office_transbank",
    tags=["BranchOfficeTransbank"]
)

@branch_office_transbank.get("/")
def index(
    page: int = Query(1, ge=1, description="Número de página"),
    items_per_page: int = Query(10, ge=1, le=100, description="Elementos por página"),
    session_user: UserLogin = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las sucursales con información de Transbank activas
    """
    data = BranchOfficeTransbankClass(db).get_all(page, items_per_page)
    return {"message": data}

@branch_office_transbank.get("/all")
def get_all_without_pagination(
    session_user: UserLogin = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las sucursales sin paginación
    """
    data = BranchOfficeTransbankClass(db).get_all(page=0)
    return {"message": data}

@branch_office_transbank.get("/{id}")
def get_by_id(
    id: int,
    session_user: UserLogin = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    """
    Obtiene una sucursal específica por ID
    """
    data = BranchOfficeTransbankClass(db).get_by_id(id)
    return {"message": data}

@branch_office_transbank.get("/search/")
def search(
    branch_office: Optional[str] = Query(None, description="Nombre de la sucursal a buscar"),
    codigo_comercio: Optional[str] = Query(None, description="Código comercio Transbank a buscar"),
    status: Optional[str] = Query(None, description="Status: 'Activo' o 'Baja'"),
    page: int = Query(1, ge=1, description="Número de página"),
    items_per_page: int = Query(10, ge=1, le=100, description="Elementos por página"),
    session_user: UserLogin = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    """
    Busca sucursales con filtros opcionales
    """
    data = BranchOfficeTransbankClass(db).search(
        branch_office=branch_office,
        codigo_comercio=codigo_comercio,
        status=status,
        page=page,
        items_per_page=items_per_page
    )
    return {"message": data}

@branch_office_transbank.put("/update_status/{branch_office_id}")
def update_transbank_status(
    branch_office_id: int,
    status: int = Query(description="Status: 0 para Activo, 1 para Baja"),
    session_user: UserLogin = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    """
    Actualiza el status de Transbank para una sucursal
    """
    if status not in [0, 1]:
        return {"message": {"status": "error", "message": "Status debe ser 0 (Activo) o 1 (Baja)"}}
    
    data = BranchOfficeTransbankClass(db).update_transbank_status(branch_office_id, status)
    return {"message": data}
