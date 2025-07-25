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
    now = datetime.now(tz)  # obtienes la fecha y hora actual en la zona horaria

    until = now.strftime('%Y-%m-%d')
    since = (now - timedelta(days=100)).strftime('%Y-%m-%d')

    branch_offices = BranchOfficeClass(db).get_with_machine()

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
                json=payload,  # ✅ Ahora pasas un dict (se serializa automáticamente)
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 200:
                dte_data = response.json()

                cashier_id = CashierClass(db).get_with_machine(branch_office.id)
                
                gross_total = 0
                total_tickets = 0
                net_total = 0

                # Totales por sucursal
                total_per_branch_office = 0
                ticket_numbers = 0

                for dte_datum in dte_data:
                    print(dte_datum["total"])
                    if dte_datum.get("sucursal_sii") == branch_office.dte_code:
                        print(232323232)
                        total_per_branch_office = total_per_branch_office + dte_datum["total"]
                        ticket_numbers = ticket_numbers + 1

                print(f"Sucursal {branch_office.dte_code} => Total: {total_per_branch_office}, Boletas: {ticket_numbers}")

    return {"status": "Redcomercio data updated successfully"}
