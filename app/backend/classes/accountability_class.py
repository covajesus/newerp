import requests
from app.backend.db.models import BranchOfficeModel, ExpenseTypeModel
import json
from calendar import monthrange

class AccountabilityClass:
    def __init__(self, db):
        self.db = db

    def delete(self, branch_office_id, period, expense_type_id):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        expense_type = self.db.query(ExpenseTypeModel).filter(ExpenseTypeModel.id == expense_type_id).first()

        if branch_office_id != None and branch_office_id != '' and branch_office_id != 0:
            branch_office_qty = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == branch_office_id).count()
        else:
            branch_office_qty = 0

        if branch_office_qty == 0:
            gloss = expense_type.accounting_account
        else:
            branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == branch_office_id).first()

            gloss = str(branch_office.branch_office) + "_" + str(expense_type.accounting_account)

        url = "https://libredte.cl/api/lce/lce_asientos/buscar/76063822"

        since_date = f"{period}-01"
        period_year = period.split("-")[0]
        # Obtener último día del mes
        year, month = map(int, period.split("-"))
        last_day = monthrange(year, month)[1]
        until_date = f"{period}-{last_day:02d}"

        payload = {
            "periodo": period_year,
            "fecha_desde": since_date,
            "fecha_hasta": until_date,
            "glosa": gloss,
            "operacion": None,
            "cuenta": expense_type.accounting_account,
            "debe": None,
            "debe_desde": None,
            "debe_hasta": None,
            "haber": None,
            "haber_desde": None,
            "haber_hasta": None
        }
        print(payload)

        headers = {
            "Content-Type": "application/json",
            'Authorization': f'Bearer {TOKEN}'
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))

        try:
            entries = response.json()
        except json.JSONDecodeError:
            print("⚠ Error al decodificar JSON de la respuesta:")
            print(response.text)
            return
        
        for entry in entries:
            entry_id = entry.get("id")
            date = entry.get("fecha")
            description = entry.get("glosa")

            # Handle "documentos" which can be a dict or a list
            documents_data = entry.get("documentos", {})
            if isinstance(documents_data, dict):
                documents = documents_data.get("emitidos", [])
            elif isinstance(documents_data, list):
                documents = documents_data
            else:
                documents = []

            dte = documents[0].get("dte") if documents else None
            folio = documents[0].get("folio") if documents else None

            details = entry.get("detalle", [])
            for item in details:
                # Optional: use 'item' data if needed
                delete_url = f"https://libredte.cl/api/lce/lce_asientos/eliminar/{period_year}/{entry_id}/76063822"

                delete_headers = {
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {TOKEN}'
                }

                delete_response = requests.get(delete_url, headers=delete_headers)

                print(delete_response.text)