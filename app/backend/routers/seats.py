from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.backend.db.database import get_db
from app.backend.schemas import SeatRefresh
from app.backend.classes.seat_class import SeatClass

router = APIRouter(prefix="/seats", tags=["seats"])

@router.post("/refresh")
async def refresh_seats(
    seat_refresh: SeatRefresh,
    db: Session = Depends(get_db)
):
    """
    Refrescar asientos contables para un período específico.
    
    Args:
        seat_refresh: Datos necesarios para el refresh (token, rut, password, mes, año)
        db: Sesión de base de datos
    
    Returns:
        Resultado del procesamiento de asientos contables
    """
    
    try:
        # Crear instancia de SeatClass y ejecutar refresh
        seat_class = SeatClass(db)
        result = seat_class.refresh(
            external_token=seat_refresh.external_token,
            rut=seat_refresh.rut,
            password=seat_refresh.password,
            month=seat_refresh.month,
            year=seat_refresh.year
        )
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error procesando asientos: {str(e)}"
        }

@router.get("/status/{year}/{month}")
async def get_seat_status(
    year: int,
    month: int,
    db: Session = Depends(get_db)
):
    """
    Obtener el estado de los asientos para un período específico.
    
    Args:
        year: Año del período
        month: Mes del período
        db: Sesión de base de datos
    
    Returns:
        Estadísticas de asientos para el período
    """
    
    from app.backend.db.models import EerrModel
    
    # Formatear período
    month_str = f"{month:02d}"
    period = f"{year}-{month_str}"
    
    # Obtener estadísticas
    total_records = db.query(EerrModel).filter(EerrModel.period == period).count()
    
    total_amount = db.query(EerrModel).filter(EerrModel.period == period).with_entities(
        EerrModel.amount
    ).all()
    
    total_sum = sum([record.amount for record in total_amount]) if total_amount else 0
    
    # Obtener por sucursal
    branch_stats = db.query(EerrModel).filter(EerrModel.period == period).all()
    branch_summary = {}
    
    for record in branch_stats:
        branch_id = record.branch_office_id
        if branch_id not in branch_summary:
            branch_summary[branch_id] = {
                "count": 0,
                "total_amount": 0
            }
        branch_summary[branch_id]["count"] += 1
        branch_summary[branch_id]["total_amount"] += record.amount
    
    return {
        "period": period,
        "total_records": total_records,
        "total_amount": total_sum,
        "branch_summary": branch_summary,
        "status": "active" if total_records > 0 else "empty"
    }
