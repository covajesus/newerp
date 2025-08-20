from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.backend.db.database import get_db
from app.backend.classes.scrapper_class import ScrapperClass

router = APIRouter(prefix="/scrappers", tags=["scrappers"])

@router.get("/customer_data/{rut}")
def get_customer_data(
    rut: str,
    force_selenium: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get customer data from SII using external API (no captcha required)
    
    Args:
        rut (str): Complete RUT with verification digit (e.g., "76063822-6")
        force_selenium (bool): Force use of Selenium instead of API (default: False)
        db (Session): Database session
    
    Returns:
        dict: Customer data obtained from SII
    """
    try:
        # Split RUT into number and verification digit
        if "-" not in rut:
            return {
                "success": False,
                "message": "Invalid RUT format. Use format: 12345678-9",
                "error": "RUT must contain hyphen separator",
                "method": "validation_error"
            }
        
        rut_parts = rut.split("-")
        if len(rut_parts) != 2:
            return {
                "success": False,
                "message": "Invalid RUT format. Use format: 12345678-9", 
                "error": "RUT must have exactly one hyphen",
                "method": "validation_error"
            }
        
        rut_number = rut_parts[0].strip()
        verification_digit = rut_parts[1].strip()
        
        # Validate RUT number contains only digits
        if not rut_number.isdigit():
            return {
                "success": False,
                "message": "Invalid RUT number. Must contain only digits",
                "error": "RUT number must be numeric",
                "method": "validation_error"
            }
        
        # Validate verification digit
        if len(verification_digit) != 1 or not (verification_digit.isdigit() or verification_digit.upper() == 'K'):
            return {
                "success": False,
                "message": "Invalid verification digit. Must be 0-9 or K",
                "error": "Verification digit must be single digit or K",
                "method": "validation_error"
            }
        
        scrapper = ScrapperClass(db)
        
        # Use API by default (no captcha), only Selenium if forced
        use_api_first = not force_selenium
        
        result = scrapper.get_customer_data(rut_number, verification_digit, use_api_first=use_api_first)
        
        if result and result.get("success"):
            return {
                "success": True,
                "message": "Data obtained successfully",
                "method": result.get("method", "external_api"),
                "captcha_required": False,  # External API doesn't require captcha
                "data": result
            }
        else:
            return {
                "success": False,
                "message": "Could not obtain customer data",
                "error": result.get("error", "Unknown error"),
                "method": result.get("method", "unknown"),
                "rut_consulted": result.get("rut_consulted", rut),
                "recommendation": result.get("recommendation", "Check connectivity with external API")
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": "Internal server error",
            "error": str(e),
            "method": "internal_error"
        }
