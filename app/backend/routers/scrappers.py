from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.backend.db.database import get_db
from app.backend.classes.scrapper_class import ScrapperClass

router = APIRouter(prefix="/scrappers", tags=["scrappers"])

@router.get("/customer_data")
def get_customer_data(
    rut_sin_dv: str = "76063822",
    dv: str = "6",
    force_selenium: bool = False,
    db: Session = Depends(get_db)
):
    """
    Obtener datos del cliente desde el SII usando API externa (sin captcha)
    
    Args:
        rut_sin_dv (str): RUT sin dígito verificador (default: "76063822")
        dv (str): Dígito verificador (default: "6")
        force_selenium (bool): Forzar uso de Selenium en lugar de API (default: False)
        db (Session): Sesión de base de datos
    
    Returns:
        dict: Datos del cliente obtenidos del SII
    """
    try:
        scrapper = ScrapperClass(db)
        
        # Por defecto usar API (sin captcha), solo Selenium si se fuerza
        use_api_first = not force_selenium
        
        result = scrapper.get_customer_data(rut_sin_dv, dv, use_api_first=use_api_first)
        
        if result and result.get("success"):
            return {
                "success": True,
                "message": "Datos obtenidos exitosamente",
                "method": result.get("method", "api_externa"),
                "captcha_required": False,  # API externa no requiere captcha
                "data": result
            }
        else:
            return {
                "success": False,
                "message": "No se pudieron obtener los datos del cliente",
                "error": result.get("error", "Error desconocido"),
                "method": result.get("method", "unknown"),
                "rut_consultado": result.get("rut_consultado", f"{rut_sin_dv}-{dv}"),
                "recomendacion": result.get("recomendacion", "Revisar conectividad con API externa")
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": "Error interno del servidor",
            "error": str(e),
            "method": "error_interno"
        }
