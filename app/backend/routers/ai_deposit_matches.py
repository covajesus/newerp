from fastapi import APIRouter, Depends, HTTPException, Query, Body
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.ai_deposit_match_class import AiDepositMatchClass
from app.backend.auth.auth_user import get_current_active_user
from app.backend.schemas import UserLogin
from typing import Optional, List

ai_deposit_matches = APIRouter(
    prefix="/ai_deposit_matches",
    tags=["AI Deposit Matches"]
)

@ai_deposit_matches.post("/find_match")
def find_match(
    bank_statement_id: Optional[int] = Query(None, description="ID del bank statement"),
    transbank_statement_id: Optional[int] = Query(None, description="ID del transbank statement"),
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Busca matches entre datos de cartola (bank_statements o transbank_statements) y depósitos usando IA
    Debe proporcionar bank_statement_id O transbank_statement_id
    """
    if not bank_statement_id and not transbank_statement_id:
        raise HTTPException(status_code=400, detail="Debe proporcionar bank_statement_id o transbank_statement_id")
    
    if bank_statement_id and transbank_statement_id:
        raise HTTPException(status_code=400, detail="Proporcione solo uno: bank_statement_id o transbank_statement_id")
    
    try:
        result = AiDepositMatchClass(db).find_matches_with_ai(
            bank_statement_id=bank_statement_id,
            transbank_statement_id=transbank_statement_id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al buscar match: {str(e)}")

@ai_deposit_matches.post("/confirm/{match_id}")
def confirm_match(
    match_id: int,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Confirma un match encontrado por IA
    """
    try:
        match = AiDepositMatchClass(db).confirm_match(match_id, user_id=session_user.id)
        return {
            "status": "success",
            "message": "Match confirmado exitosamente",
            "match_id": match.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al confirmar match: {str(e)}")

@ai_deposit_matches.post("/reject/{match_id}")
def reject_match(
    match_id: int,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Rechaza un match encontrado por IA
    """
    try:
        match = AiDepositMatchClass(db).reject_match(match_id, user_id=session_user.id)
        return {
            "status": "success",
            "message": "Match rechazado exitosamente",
            "match_id": match.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al rechazar match: {str(e)}")

@ai_deposit_matches.get("/list")
def list_matches(
    is_confirmed: Optional[bool] = Query(None, description="Filtrar por confirmados"),
    is_rejected: Optional[bool] = Query(None, description="Filtrar por rechazados"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación"),
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Lista los matches encontrados por IA
    """
    try:
        result = AiDepositMatchClass(db).get_matches(
            is_confirmed=is_confirmed,
            is_rejected=is_rejected,
            limit=limit,
            offset=offset
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar matches: {str(e)}")

@ai_deposit_matches.post("/process_batch_bank_statements")
def process_batch_bank_statements(
    bank_statement_ids: List[int] = Body(..., description="Lista de IDs de bank statements"),
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Procesa múltiples bank_statements en lote para encontrar matches con IA
    """
    if not bank_statement_ids:
        raise HTTPException(status_code=400, detail="Debe proporcionar al menos un bank_statement_id")
    
    results = {
        "processed": 0,
        "matched": 0,
        "no_match": 0,
        "errors": []
    }
    
    for bank_statement_id in bank_statement_ids:
        try:
            result = AiDepositMatchClass(db).find_matches_with_ai(bank_statement_id=bank_statement_id)
            results["processed"] += 1
            
            if result.get("status") == "success":
                results["matched"] += 1
            else:
                results["no_match"] += 1
                
        except Exception as e:
            results["errors"].append({
                "bank_statement_id": bank_statement_id,
                "error": str(e)
            })
    
    return results

@ai_deposit_matches.post("/process_all_pending_bank_statements")
def process_all_pending_bank_statements(
    limit: Optional[int] = Query(None, description="Límite de registros a procesar (opcional)"),
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Procesa automáticamente todos los bank_statements pendientes que no tienen match confirmado.
    Analiza registro por registro con IA contra depósitos no aceptados.
    """
    try:
        result = AiDepositMatchClass(db).process_all_pending_bank_statements(limit=limit)
        return {
            "status": "success",
            "message": f"Procesados {result['total_processed']} registros",
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar bank statements pendientes: {str(e)}")

@ai_deposit_matches.post("/process_all_pending_transbank_statements")
def process_all_pending_transbank_statements(
    limit: Optional[int] = Query(None, description="Límite de registros a procesar (opcional)"),
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Procesa automáticamente todos los transbank_statements pendientes que no tienen match confirmado.
    Analiza registro por registro con IA contra depósitos no aceptados.
    """
    try:
        result = AiDepositMatchClass(db).process_all_pending_transbank_statements(limit=limit)
        return {
            "status": "success",
            "message": f"Procesados {result['total_processed']} registros",
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar transbank statements pendientes: {str(e)}")
