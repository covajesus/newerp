from fastapi import APIRouter, Depends, HTTPException, Query, Response, Request
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.preventive_maintenance_class import PreventiveMaintenanceClass
from app.backend.schemas import (
    PreventiveMaintenanceCreate,
    PreventiveMaintenanceUpdate,
    PreventiveMaintenanceResponse,
    PreventiveMaintenanceSectionResponse,
    PreventiveMaintenanceItemResponse,
    PreventiveMaintenanceWithDetails,
    PreventiveMaintenanceList
)
from app.backend.auth.auth_user import get_current_active_user
from app.backend.schemas import UserLogin
from typing import Optional, List

preventive_maintenances = APIRouter(
    prefix="/preventive_maintenances",
    tags=["Preventive Maintenances"]
)

# ========== PREVENTIVE MAINTENANCE ENDPOINTS ==========

@preventive_maintenances.post("/")
def index(
    preventive_maintenance_list: PreventiveMaintenanceList,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener todos los mantenimientos preventivos con paginación"""
    try:
        page = preventive_maintenance_list.page if preventive_maintenance_list.page > 0 else 1
        data = PreventiveMaintenanceClass(db).get_all_preventive_maintenances(
            branch_office_id=preventive_maintenance_list.branch_office_id,
            page=page,
            items_per_page=10
        )
        return {"message": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener mantenimientos preventivos: {str(e)}")

@preventive_maintenances.post("/store")
async def store(
    request: Request,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crear un nuevo mantenimiento preventivo"""
    try:
        # Recibir los datos como JSON para capturar todos los campos, incluyendo section1, section2, etc.
        data = await request.json()
        
        # Debug: ver qué datos se están recibiendo
        print(f"DEBUG router store: data recibido (keys): {list(data.keys())}")
        print(f"DEBUG router store: tiene section1: {'section1' in data}")
        print(f"DEBUG router store: responses en data: {data.get('responses', [])}")
        
        preventive_maintenance = PreventiveMaintenanceClass(db).create_preventive_maintenance(data)
        # Construir respuesta con maintenance_date como string
        response_data = {
            "id": preventive_maintenance.id,
            "branch_office_id": preventive_maintenance.branch_office_id,
            "address": preventive_maintenance.address,
            "maintenance_date": preventive_maintenance.maintenance_date.strftime('%Y-%m-%d') if preventive_maintenance.maintenance_date else None,
            "technician_name": preventive_maintenance.technician_name,
            "manager_name": preventive_maintenance.manager_name,
            "detected_failures": preventive_maintenance.detected_failures,
            "corrective_actions": preventive_maintenance.corrective_actions,
            "technician_signature": preventive_maintenance.technician_signature,
            "manager_signature": preventive_maintenance.manager_signature,
            "created_at": preventive_maintenance.created_at,
            "updated_at": preventive_maintenance.updated_at
        }
        return {"message": response_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear mantenimiento preventivo: {str(e)}")

@preventive_maintenances.get("/{maintenance_id}", response_model=PreventiveMaintenanceResponse)
def get_preventive_maintenance(
    maintenance_id: int,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener un mantenimiento preventivo por ID"""
    try:
        preventive_maintenance = PreventiveMaintenanceClass(db).get_preventive_maintenance(maintenance_id)
        return preventive_maintenance
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener mantenimiento preventivo: {str(e)}")

@preventive_maintenances.get("/{maintenance_id}/with_responses", response_model=dict)
def get_preventive_maintenance_with_responses(
    maintenance_id: int,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener un mantenimiento preventivo con todas sus respuestas y detalles"""
    try:
        result = PreventiveMaintenanceClass(db).get_maintenance_with_responses(maintenance_id)
        return {"message": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener mantenimiento con respuestas: {str(e)}")

@preventive_maintenances.put("/{maintenance_id}", response_model=PreventiveMaintenanceResponse)
def update_preventive_maintenance(
    maintenance_id: int,
    form_data: PreventiveMaintenanceUpdate,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualizar un mantenimiento preventivo"""
    try:
        data = form_data.dict(exclude_unset=True)
        preventive_maintenance = PreventiveMaintenanceClass(db).update_preventive_maintenance(maintenance_id, data)
        return preventive_maintenance
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar mantenimiento preventivo: {str(e)}")

@preventive_maintenances.delete("/{maintenance_id}")
def delete_preventive_maintenance(
    maintenance_id: int,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Eliminar un mantenimiento preventivo"""
    try:
        result = PreventiveMaintenanceClass(db).delete_preventive_maintenance(maintenance_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar mantenimiento preventivo: {str(e)}")

# ========== SECTION ENDPOINTS ==========

@preventive_maintenances.get("/sections", response_model=List[PreventiveMaintenanceSectionResponse])
def get_all_sections(
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener todas las secciones"""
    try:
        sections = PreventiveMaintenanceClass(db).get_all_sections(is_active=is_active)
        return sections
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener secciones: {str(e)}")

@preventive_maintenances.get("/sections/{section_id}", response_model=PreventiveMaintenanceSectionResponse)
def get_section(
    section_id: int,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener una sección por ID"""
    try:
        section = PreventiveMaintenanceClass(db).get_section(section_id)
        return section
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener sección: {str(e)}")

# ========== ITEM ENDPOINTS ==========

@preventive_maintenances.get("/items", response_model=List[PreventiveMaintenanceItemResponse])
def get_all_items(
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener todos los items"""
    try:
        items = PreventiveMaintenanceClass(db).get_all_items(is_active=is_active)
        return items
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener items: {str(e)}")

@preventive_maintenances.get("/items/section/{section_id}", response_model=List[PreventiveMaintenanceItemResponse])
def get_items_by_section(
    section_id: int,
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener todos los items de una sección"""
    try:
        items = PreventiveMaintenanceClass(db).get_items_by_section(section_id, is_active=is_active)
        return items
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener items: {str(e)}")

@preventive_maintenances.get("/items/{item_id}", response_model=PreventiveMaintenanceItemResponse)
def get_item(
    item_id: int,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener un item por ID"""
    try:
        item = PreventiveMaintenanceClass(db).get_item(item_id)
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener item: {str(e)}")

# ========== RESPONSE ENDPOINTS ==========

@preventive_maintenances.get("/{maintenance_id}/responses", response_model=List[dict])
def get_responses_by_maintenance(
    maintenance_id: int,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener todas las respuestas de un mantenimiento preventivo"""
    try:
        responses = PreventiveMaintenanceClass(db).get_responses_by_maintenance(maintenance_id)
        return responses
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener respuestas: {str(e)}")

@preventive_maintenances.get("/{maintenance_id}/download_pdf")
def download_pdf(
    maintenance_id: int,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Descargar PDF del mantenimiento preventivo"""
    try:
        pdf_bytes = PreventiveMaintenanceClass(db).generate_pdf(maintenance_id)
        
        # Obtener datos del mantenimiento para el nombre del archivo
        maintenance = PreventiveMaintenanceClass(db).get_preventive_maintenance(maintenance_id)
        date_str = maintenance.maintenance_date.strftime('%Y%m%d') if maintenance.maintenance_date else 'unknown'
        filename = f"mantencion_preventiva_{maintenance_id}_{date_str}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar PDF: {str(e)}")
