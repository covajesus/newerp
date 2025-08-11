from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from app.backend.classes.branch_office_class import BranchOfficeClass
from sqlalchemy.orm import Session
import requests
from app.backend.classes.collection_class import CollectionClass
from app.backend.classes.cashier_class import CashierClass
from datetime import date, datetime
from datetime import timedelta
import pytz

redcomercio_data = APIRouter(
    prefix="/redcomercio_data",
    tags=["Redcomercio_data"]
)

@redcomercio_data.get("/refresh")
def refresh(db: Session = Depends(get_db)):
    TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

    url = "https://libredte.cl/api/dte/dte_emitidos/buscar/76063822-6"

    tz = pytz.timezone('America/Santiago')
    now = datetime.now(tz)

    until = now.strftime('%Y-%m-%d')
    since = (now - timedelta(days=90)).strftime('%Y-%m-%d')

    branch_offices = BranchOfficeClass(db).get_with_machine()

    # Diccionario para agrupar por (cashier_id, branch_office_id, fecha)
    grouped_data = {}

    if isinstance(branch_offices, list):
        for branch_office in branch_offices:
            payload = {
                "dte": ["39"],
                "fecha_desde": since,
                "fecha_hasta": until,
                "sucursal_sii": branch_office.dte_code,
            }

            response = requests.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 200:
                dte_data = response.json()
                cashier_id = CashierClass(db).get_with_machine(branch_office.id)

                for dte_datum in dte_data:
                    added_date = dte_datum['fecha']
                    key = (cashier_id, branch_office.id, added_date)
                    total = dte_datum['total']

                    if key not in grouped_data:
                        grouped_data[key] = {
                            "gross_total": 0,
                            "total_tickets": 0
                        }
                    grouped_data[key]["gross_total"] += total
                    grouped_data[key]["total_tickets"] += 1

    # Ahora recorre el diccionario y haz insert/update
    for (cashier_id, branch_office_id, added_date), values in grouped_data.items():
        gross_total = values["gross_total"]
        net_total = round(gross_total / 1.19)
        total_tickets = values["total_tickets"]

        cash_gross_amount = CollectionClass(db).delete_red_comercio_collection(branch_office_id, cashier_id, added_date)
        print(cashier_id)
        print(branch_office_id)
        print(gross_total)
        print(net_total)
        print(total_tickets)
        print(added_date)
        if cash_gross_amount is None or cash_gross_amount == 0:
            CollectionClass(db).store_redcomercio(cashier_id, branch_office_id, gross_total, net_total, total_tickets, added_date)
        else:
            gross_total += cash_gross_amount
            net_total = round(gross_total / 1.19)
            CollectionClass(db).update_redcomercio(cashier_id, branch_office_id, gross_total, net_total, total_tickets, added_date)

    return {"status": "Redcomercio data updated successfully"}

