import requests
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.backend.db.database import get_db
from app.backend.classes.authentication_class import AuthenticationClass
from app.backend.schemas import ExternalApiCredentials

summary_indicators = APIRouter(
    prefix="/summary-indicators",
    tags=["Summary Indicators"]
)

def make_request_with_fresh_token_if_needed(url: str, credentials: ExternalApiCredentials, db: Session):
    """Función helper que intenta usar el token actual, y si falla (401 o token-invalido) genera uno nuevo"""
    
    # Primero intentar con el token actual
    headers = {'Authorization': f'Bearer {credentials.external_token}'}
    response = requests.get(url, headers=headers)
    
    # Si el token está vencido (401) o el mensaje contiene "token-invalido", crear uno nuevo
    if response.status_code == 401 or "token-invalido" in response.text.lower():
        fresh_token = AuthenticationClass(db).create_external_token(credentials.rut, credentials.password)
        headers = {'Authorization': f'Bearer {fresh_token}'}
        response = requests.get(url, headers=headers)
    
    return response

@summary_indicators.post("/summary")
def get_summary_indicators(credentials: ExternalApiCredentials, db: Session = Depends(get_db)):
    """
    Obtiene resumen de indicadores económicos desde la API externa
    """
    url = "https://api.jisreportes.com/indicadores/summary"
    response = make_request_with_fresh_token_if_needed(url, credentials, db)
    return {"message": response.text}
