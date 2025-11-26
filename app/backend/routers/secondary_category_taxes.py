# Dentro de la función scrape() en tu servidor FastAPI


from fastapi import APIRouter, Depends
import httpx
from bs4 import BeautifulSoup
import requests
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin
from app.backend.classes.payroll_indicator_class import PayrollIndicatorClass
from app.backend.classes.payroll_uf_indicator_class import PayrollUfIndicatorClass
from app.backend.classes.helper_class import HelperClass
from app.backend.auth.auth_user import get_current_active_user

secondary_category_taxes = APIRouter(
    prefix="/secondary_category_taxes",
    tags=["secondary_category_taxes"]
)

@secondary_category_taxes.get("/scrape/{period}")
async def scrape(period:str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:

        # Define la URL del sitio web
        url = 'https://transtecnia.cl/impuesto-unico-chile/'

        # Hacer la solicitud POST al sitio web con los datos del formulario
        response = requests.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')

        td_elements = soup.find_all('td')

        # Crea una lista vacía para almacenar los datos
        data = []

        for td in td_elements:
            datum = HelperClass().remove_from_string("$", td.text)

            data.append(datum)

        return data
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": "Error en el servidor"}