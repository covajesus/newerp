from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from app.backend.routers.branch_offices import branch_offices
from app.backend.routers.genders import genders
from app.backend.routers.nationalities import nationalities
from app.backend.routers.pentions import pentions
from app.backend.routers.banks import banks
from app.backend.routers.account_types import account_types
from app.backend.routers.regions import regions
from app.backend.routers.employees import employees
from app.backend.routers.slider import slider
from app.backend.routers.logo import logo
from app.backend.routers.users import users
from app.backend.routers.employee_labor_data import employee_labor_data
from app.backend.routers.employee_extras import employee_extras
from app.backend.routers.alert_types import alert_types
from app.backend.routers.patology_types import patology_types
from app.backend.routers.civil_states import civil_states
from app.backend.routers.document_types import document_types
from app.backend.routers.family_core_data import family_core_data
from app.backend.routers.vacations import vacations
from app.backend.routers.rols import rols
from app.backend.routers.communes import communes
from app.backend.routers.budgets import budgets
from app.backend.routers.collections import collections
from app.backend.routers.dtes import dtes
from fastapi.middleware.cors import CORSMiddleware
from app.backend.routers.employee_types import employee_types
from app.backend.routers.regimes import regimes
from app.backend.routers.alerts import alerts
from app.backend.routers.deposits import deposits
from app.backend.routers.folios import folios
from app.backend.routers.files import files
from app.backend.routers.contracts import contracts
from app.backend.routers.taxes import taxes
from app.backend.routers.months import months
from app.backend.routers.patents import patents
from app.backend.routers.customers import customers
from app.backend.routers.cafs import cafs
from app.backend.routers.customer_tickets import customer_tickets
from app.backend.routers.customer_bills import customer_bills
from app.backend.routers.machine_tickets import machine_tickets
from app.backend.routers.supervisors import supervisors
from app.backend.routers.expense_types import expense_types
from app.backend.routers.received_tributary_documents import received_tributary_documents
from app.backend.routers.customer_tickets_bills import customer_tickets_bills
from app.backend.routers.cashiers import cashiers
from app.backend.routers.biller_data import biller_data
from app.backend.routers.settings import settings
from app.backend.routers.carbon_monoxides import carbon_monoxides
from app.backend.routers.sinisters import sinisters
from app.backend.routers.bank_statements import bank_statements
from app.backend.routers.authentications import authentications
from app.backend.routers.capitulations import capitulations
from app.backend.routers.cash_reserves import cash_reserves
from app.backend.routers.interships import interships
from app.backend.routers.honorary_reasons import honorary_reasons
from app.backend.routers.employee_interships import employee_interships
from app.backend.routers.honoraries import honoraries
from app.backend.routers.demarcations import demarcations
from app.backend.routers.customer_collections import customer_collections
from app.backend.routers.maintenances import maintenances
from app.backend.routers.redcomercio_data import redcomercio_data
from app.backend.routers.transbank_statements import transbank_statements
from app.backend.routers.segments import segments
from app.backend.routers.zones import zones
from app.backend.routers.principals import principals
from app.backend.routers.group_details import group_details
from app.backend.routers.accountability import accountability
from app.backend.routers.remuneration import remuneration
from app.backend.routers.suppliers import suppliers

app = FastAPI(root_path="/api")
application = app

# FILES_DIR = "C:/Users/jesus/OneDrive/Desktop/escritorio/newerp/files"

# Montar como directorio estático
# app.mount("/files", StaticFiles(directory=FILES_DIR), name="files")

os.environ['SECRET_KEY'] = '7de4c36b48fce8dcb3a4bb527ba62d789ebf3d3a7582472ee49d430b01a7f868'
os.environ['ALGORITHM'] = 'HS256'

origins = [
    "*",
    "https://newerp-ghdegyc9cpcpc6gq.eastus-01.azurewebsites.net",
    
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(branch_offices)
app.include_router(genders)
app.include_router(nationalities)
app.include_router(pentions)
app.include_router(banks)
app.include_router(account_types)
app.include_router(regions)
app.include_router(employees)
app.include_router(slider)
app.include_router(logo)
app.include_router(users)
app.include_router(employee_labor_data)
app.include_router(employee_extras)
app.include_router(alert_types)
app.include_router(patology_types)
app.include_router(civil_states)
app.include_router(document_types)
app.include_router(family_core_data)
app.include_router(vacations)
app.include_router(rols)
app.include_router(communes)
app.include_router(budgets)
app.include_router(collections)
app.include_router(dtes)
app.include_router(employee_types)
app.include_router(regimes)
app.include_router(alerts)
app.include_router(deposits)
app.include_router(folios)
app.include_router(files)
app.include_router(contracts)
app.include_router(taxes)
app.include_router(months)
app.include_router(patents)
app.include_router(customers)
app.include_router(cafs)
app.include_router(customer_tickets)
app.include_router(customer_bills)
app.include_router(machine_tickets)
app.include_router(supervisors)
app.include_router(expense_types)
app.include_router(received_tributary_documents)
app.include_router(customer_tickets_bills)
app.include_router(cashiers)
app.include_router(biller_data)
app.include_router(settings)
app.include_router(carbon_monoxides)
app.include_router(sinisters)
app.include_router(bank_statements)
app.include_router(authentications)
app.include_router(capitulations)
app.include_router(cash_reserves)
app.include_router(interships)
app.include_router(honorary_reasons)
app.include_router(employee_interships)
app.include_router(honoraries)
app.include_router(demarcations)
app.include_router(customer_collections)
app.include_router(maintenances)
app.include_router(redcomercio_data)
app.include_router(transbank_statements)
app.include_router(segments)
app.include_router(zones)
app.include_router(principals)
app.include_router(group_details)
app.include_router(accountability)
app.include_router(remuneration)
app.include_router(suppliers)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
