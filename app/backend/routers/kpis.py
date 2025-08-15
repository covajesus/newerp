import requests
from fastapi import APIRouter
from app.backend.schemas import ExternalToken

kpis = APIRouter(
    prefix="/kpis",
    tags=["kpis"]
)

@kpis.post("/deposits")
def deposits(external_token: ExternalToken):
    url = "https://api.jisreportes.com/dashboard/kpi/depositos"

    payload={}
    headers = {
    'Authorization': 'Bearer ' + str(external_token.external_token)
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)


    return {"message": response.text}

@kpis.post("/dtes")
def dtes(external_token: ExternalToken):
    url = "https://api.jisreportes.com/dashboard/kpi/dtes"

    payload={}
    headers = {
        'Authorization': 'Bearer ' + str(external_token.external_token)
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)


    return {"message": response.text}


@kpis.post("/budgets")
def budgets(external_token: ExternalToken):
    url = "https://api.jisreportes.com/dashboard/kpi/presupuesto"

    payload={}
    headers = {
        'Authorization': 'Bearer ' + str(external_token.external_token)
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)


    return {"message": response.text}

@kpis.post("/sales")
def sales(external_token: ExternalToken):
    url = "https://api.jisreportes.com/dashboard/kpi/ventas"

    payload={}
    headers = {
        'Authorization': 'Bearer ' + str(external_token.external_token)
    }
    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)


    return {"message": response.text}