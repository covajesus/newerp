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
            assets = response.json()
            print(assets)
        except json.JSONDecodeError:
            print("⚠ Error al decodificar JSON de la respuesta:")
            print(response.text)
            return
        
        for asset in assets:
            asset_id = asset.get("id")
            fecha = asset.get("fecha")
            glosa = asset.get("glosa")

            documentos = asset.get("documentos", {}).get("emitidos", [])
            dte = documentos[0].get("dte") if documentos else None
            folio = documentos[0].get("folio") if documentos else None

            detalle = asset.get("detalle", [])
            for item in detalle:
                asset_id

                url = "https://libredte.cl/api/lce/lce_asientos/eliminar/" + str(period_year) +"/" + str(asset_id) + "/76063822"

                payload={}
                headers = {
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {TOKEN}'
                }


                response = requests.request("GET", url, headers=headers, data=payload)

                print(response.text)
