import requests
from app.backend.db.models import BranchOfficeModel
import json
from calendar import monthrange

class AccountabilityClass:
    def __init__(self, db):
        self.db = db

    def delete(self, branch_office_id, period):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        branch_office_qty = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == branch_office_id).count()

        if branch_office_qty == 0:
            gloss = "441000102"
        else:
            branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == branch_office_id).first()

            gloss = str(branch_office.branch_office) + "_441000102"

        url = "https://libredte.cl/api/lce/lce_asientos/buscar/76063822"

        since_date = f"{period}-01"
        # Obtener último día del mes
        year, month = map(int, period.split("-"))
        last_day = monthrange(year, month)[1]
        until_date = f"{period}-{last_day:02d}"

        payload = {
            "periodo": period,
            "fecha_desde": since_date,
            "fecha_hasta": until_date,
            "glosa": gloss,
            "operacion": None,
            "cuenta": '441000102',
            "debe": None,
            "debe_desde": None,
            "debe_hasta": None,
            "haber": None,
            "haber_desde": None,
            "haber_hasta": None
        }

        headers = {
            "Content-Type": "application/json",
            'Authorization': f'Bearer {TOKEN}'
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))

        print(response.status_code)
        print(response.text)
