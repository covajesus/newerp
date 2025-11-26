from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from app.backend.classes.folio_class import FolioClass
from app.backend.classes.caf_class import CafClass
from app.backend.db.database import get_db, get_db2
from sqlalchemy.orm import Session
from app.backend.schemas import CafList, UserLogin
from app.backend.auth.auth_user import get_current_active_user
from pydantic import BaseModel

class ManualCafRequest(BaseModel):
    branch_office_id: int
    cashier_id: int
    quantity: int

cafs = APIRouter(
    prefix="/cafs",
    tags=["Cafs"]
)

@cafs.post("/")
def get_all(caf: CafList, db: Session = Depends(get_db)):

    data = FolioClass(db).get_all(caf)

    return {"message": data}

@cafs.post("/manual")
def manual_caf(request: ManualCafRequest, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db), db2: Session = Depends(get_db2)):
    """
    Crear CAF manual con los parámetros especificados y devolver archivo SQL para descarga
    """
    try:
        result = CafClass(db, db2).manual(request.branch_office_id, request.cashier_id, request.quantity)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        # Obtener contenido SQL para descarga
        sql_content = result["data"]["sql_content"]
        folio_min = result["data"]["folio_min"]
        folio_max = result["data"]["folio_max"]
        
        # Crear respuesta de descarga del archivo SQL
        filename = f"caf_manual_{folio_min}_{folio_max}.sql"
        
        return Response(
            content=sql_content,
            media_type="application/sql",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating manual CAF: {str(e)}")