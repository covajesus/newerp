from fastapi import FastAPI
import uvicorn
import os
from app.backend.routers.branch_offices import branch_offices
from app.backend.routers.genders import genders
from app.backend.routers.nationalities import nationalities
from app.backend.routers.pentions import pentions
from app.backend.routers.banks import banks
from app.backend.routers.turns import turns
from app.backend.routers.schedule import schedule
from app.backend.routers.account_types import account_types
from app.backend.routers.regions import regions
from app.backend.routers.employees import employees
from app.backend.routers.slider import slider
from app.backend.routers.logo import logo
from app.backend.routers.about_us import about_us
from app.backend.routers.contacts import contacts
from app.backend.routers.blog import blog
from app.backend.routers.frecuent_questions import frecuent_questions
from app.backend.routers.possible_employees import possible_employees
from app.backend.routers.users import users
from app.backend.routers.employee_labor_data import employee_labor_data
from app.backend.routers.employee_extras import employee_extras
from app.backend.routers.alert_types import alert_types
from app.backend.routers.honoraries import honoraries
from app.backend.routers.uniform_types import uniform_types
from app.backend.routers.uniforms import uniforms
from app.backend.routers.segments import segments
from app.backend.routers.job_positions import job_positions
from app.backend.routers.patology_types import patology_types
from app.backend.routers.civil_states import civil_states
from app.backend.routers.document_types import document_types
from app.backend.routers.family_core_data import family_core_data
from app.backend.routers.vacations import vacations
from app.backend.routers.rols import rols
from app.backend.routers.communes import communes
from app.backend.routers.contract_data import contract_data
from app.backend.routers.contract_types import contract_types
from app.backend.routers.medical_license_types import medical_license_types
from app.backend.auth.login_users import login_users
from app.backend.routers.clock_users import clock_users
from app.backend.routers.budgets import budgets
from app.backend.routers.collections import collections
from app.backend.routers.dtes import dtes
from app.backend.routers.letter_types import letter_types
from app.backend.routers.end_documents import end_documents
from app.backend.routers.mesh_data import mesh_data
from app.backend.routers.kardex_data import kardex_data
from app.backend.routers.honorary_reasons import honorary_reasons
from fastapi.middleware.cors import CORSMiddleware
from app.backend.routers.progressive_vacations import progressive_vacations
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

app = FastAPI()

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
app.include_router(turns)
app.include_router(schedule)
app.include_router(account_types)
app.include_router(regions)
app.include_router(employees)
app.include_router(slider)
app.include_router(logo)
app.include_router(about_us)
app.include_router(contacts)
app.include_router(blog)
app.include_router(frecuent_questions)
app.include_router(possible_employees)
app.include_router(users)
app.include_router(employee_labor_data)
app.include_router(employee_extras)
app.include_router(alert_types)
app.include_router(honoraries)
app.include_router(uniform_types)
app.include_router(uniforms)
app.include_router(segments)
app.include_router(job_positions)
app.include_router(patology_types)
app.include_router(civil_states)
app.include_router(document_types)
app.include_router(family_core_data)
app.include_router(vacations)
app.include_router(rols)
app.include_router(communes)
app.include_router(contract_data)
app.include_router(contract_types)
app.include_router(medical_license_types)
app.include_router(login_users)
app.include_router(clock_users)
app.include_router(budgets)
app.include_router(collections)
app.include_router(dtes)
app.include_router(letter_types)
app.include_router(end_documents)
app.include_router(mesh_data)
app.include_router(kardex_data)
app.include_router(honorary_reasons)
app.include_router(progressive_vacations)
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

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
