from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin, StoreManualSeat
from app.backend.classes.accountability_class import AccountabilityClass
from app.backend.auth.auth_user import get_current_active_user
from app.backend.classes.file_class import FileClass
from fastapi import UploadFile, File, HTTPException
from datetime import datetime
import uuid

accountability = APIRouter(
    prefix="/accountability",
    tags=["Accountability"]
)

@accountability.post("/store")
def store(manual_seat:StoreManualSeat, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AccountabilityClass(db).store(manual_seat.branch_office_id, manual_seat.expense_type_id, manual_seat.tax_status_id, manual_seat.period, manual_seat.amount)

    return {"message": data}

@accountability.get("/delete/{branch_office_id}/{period}/{expense_type_id}")
def delete(branch_office_id: int, period: str, expense_type_id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AccountabilityClass(db).delete(branch_office_id, period, expense_type_id)

    return {"message": data}

@accountability.get("/subscriber_assets/store/{branch_office_id}/{period}")
def store_subscriber_assets(branch_office_id: int, period: str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AccountabilityClass(db).store_subscriber_assets(branch_office_id, period)

    return {"message": data}

@accountability.get("/subscriber_assets/delete/{branch_office_id}/{period}")
def delete_subscriber_assets(branch_office_id: int, period: str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = AccountabilityClass(db).delete_subscriber_assets(branch_office_id, period)

    return {"message": data}

@accountability.post("/massive_store")
def store(
    support: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
        file_category_name = 'accountability'
        unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

        remote_path = f"{file_category_name}_{unique_filename}"

        message = FileClass(db).upload(support, remote_path)

        file_url = FileClass(db).get(remote_path)

        if file_extension == "xlsx":
            excel_data = AccountabilityClass(db).read_store_massive_accountability(file_url)
        else:
            raise HTTPException(status_code=400, detail="Formato no compatible")

        return {"message": message, "file_url": file_url, "data": excel_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")

@accountability.get("/income_assets/data/{period}")
def get_monthly_collections_data(period: str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Obtiene datos de collections agrupados por sucursal y mes
    """
    try:
        data = AccountabilityClass(db).get_monthly_collections_data(period)
        
        # Convertir a formato JSON serializable
        result = []
        for row in data:
            result.append({
                "branch_office_id": row.branch_office_id,
                "ingresos": float(row.ingresos),
                "subscribers_total": int(row.subscribers_total),
                "year": int(row.year),
                "month": int(row.month)
            })
        
        return {"status": "success", "data": result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener datos: {str(e)}")

@accountability.post("/income_assets/store/{period}")
def store_branch_office_incomes(period: str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Procesa los ingresos por sucursal para un período específico
    Crea asientos contables con banco, ingresos por venta e IVA
    """
    try:
        results = AccountabilityClass(db).store_branch_office_incomes(period)
        
        return {
            "status": "success", 
            "message": f"Asientos de ingresos procesados para el período {period}",
            "processed_branches": len(results),
            "details": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar ingresos: {str(e)}")

@accountability.delete("/income_assets/delete/{period}")
def delete_income_assets(period: str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Elimina asientos de ingresos para un período específico
    """
    try:
        AccountabilityClass(db).delete_income_assets(period)
        
        return {
            "status": "success", 
            "message": f"Asientos de ingresos eliminados para el período {period}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar asientos: {str(e)}")

@accountability.post("/assets/store/{period}")
def store_all_assets(period: str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Procesa TODOS los activos (ingresos y abonados) para un período específico
    1. Elimina asientos existentes de ingresos y abonados
    2. Crea asientos de ingresos por ventas (banco, ingresos, IVA)
    3. Crea asientos de abonados (banco, ingresos abonados, IVA)
    """
    try:
        results = AccountabilityClass(db).store_all_assets(period)
        
        summary = {
            "status": "success",
            "period": period,
            "summary": {
                "eliminated_income_assets": len(results["eliminated_income_assets"]),
                "eliminated_subscriber_assets": len(results["eliminated_subscriber_assets"]),
                "created_income_assets": len(results["created_income_assets"]),
                "created_subscriber_assets": len(results["created_subscriber_assets"]),
                "errors": len(results["errors"])
            },
            "message": f"Procesamiento completo de activos finalizado para {period}",
            "details": results
        }
        
        return summary
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar activos: {str(e)}")

@accountability.get("/test/libredte")
def test_libredte_response(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Endpoint de prueba para ver qué devuelve LibreDTE
    """
    try:
        result = AccountabilityClass(db).test_libredte_response()
        
        return {
            "status": "success",
            "message": "Consulta de prueba a LibreDTE completada",
            "data": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en prueba LibreDTE: {str(e)}")

@accountability.get("/delete_seats/{period}")
def delete_seats_by_period(period: str, db: Session = Depends(get_db)):
    """
    Elimina asientos contables que contengan NotaCredito, Factura o BoletaElectronica para un período específico
    """
    try:
        result = AccountabilityClass(db).delete_seats_by_period(period)
        
        return {
            "status": "success",
            "period": period,
            "message": f"Eliminación de asientos completada para el período {period}",
            "details": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar asientos: {str(e)}")
