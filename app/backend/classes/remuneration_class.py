import requests
from app.backend.db.models import BranchOfficeModel, ExpenseTypeModel
from app.backend.classes.helper_class import HelperClass
from fastapi import HTTPException
from io import BytesIO
import pandas as pd
from app.backend.db.models import RemunerationModel

class RemunerationClass:
    def __init__(self, db):
        self.db = db

    def read_store_massive_accountability(self, file_url):
        try:
            token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
            response = requests.get(file_url)
            response.raise_for_status()

            excel_file = BytesIO(response.content)
            xls = pd.ExcelFile(excel_file, engine="openpyxl")
            sheet_names = xls.sheet_names

            if not sheet_names:
                raise HTTPException(status_code=500, detail="El archivo Excel no tiene hojas.")

            df = pd.read_excel(xls, sheet_name=sheet_names[0], engine="openpyxl")
            df = df.fillna("")

            for index, row in df.iterrows():
                try:
                    branch_office_id = row["SUCURSAL"]
                    accounting_account = row["TIPO DE GASTO"]
                    amount = float(row["MONTO"])
                    period = int(row["PERIODO"])

                    remuneration = RemunerationModel()
                    remuneration.branch_office_id = branch_office_id
                    remuneration.accounting_account = accounting_account
                    remuneration.amount = amount
                    remuneration.period = period
                    remuneration.added_date = HelperClass.get_current_datetime()
                    self.db.add(remuneration)
                    self.db.commit()

                except Exception as row_error:
                    print(f"[Fila {index + 2}] Error procesando fila: {row_error}")

            return {"status": "success", "message": "Proceso completado"}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")
