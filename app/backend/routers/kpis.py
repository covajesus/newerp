import requests
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.backend.db.database import get_db
from app.backend.classes.authentication_class import AuthenticationClass
from app.backend.schemas import ExternalApiCredentials

kpis = APIRouter(
    prefix="/kpis",
    tags=["kpis"]
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

@kpis.post("/deposits")
def deposits(credentials: ExternalApiCredentials, db: Session = Depends(get_db)):
    url = "https://api.jisreportes.com/dashboard/kpi/depositos"
    response = make_request_with_fresh_token_if_needed(url, credentials, db)
    return {"message": response.text}

@kpis.post("/dtes")
def dtes(credentials: ExternalApiCredentials, db: Session = Depends(get_db)):
    url = "https://api.jisreportes.com/dashboard/kpi/dtes"
    response = make_request_with_fresh_token_if_needed(url, credentials, db)
    return {"message": response.text}

@kpis.post("/budgets")
def budgets(credentials: ExternalApiCredentials, db: Session = Depends(get_db)):
    url = "https://api.jisreportes.com/dashboard/kpi/presupuesto"
    response = make_request_with_fresh_token_if_needed(url, credentials, db)
    return {"message": response.text}

@kpis.post("/sales")
def sales(credentials: ExternalApiCredentials, db: Session = Depends(get_db)):
    url = "https://api.jisreportes.com/dashboard/kpi/ventas"
    response = make_request_with_fresh_token_if_needed(url, credentials, db)
    return {"message": response.text}

@kpis.post("/get_daily_summary_indicadores_summary_get")
def get_daily_summary_indicadores_summary_get(credentials: ExternalApiCredentials, db: Session = Depends(get_db)):
    url = "https://api.jisreportes.com/docs#/Indicadores%20Econ%C3%B3micos/get_daily_summary_indicadores_summary_get"
    response = make_request_with_fresh_token_if_needed(url, credentials, db)
    return {"message": response.text}