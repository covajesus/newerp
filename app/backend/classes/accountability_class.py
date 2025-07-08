import requests
from app.backend.db.models import BranchOfficeModel, ExpenseTypeModel, CollectionModel
import json
from calendar import monthrange
from app.backend.classes.helper_class import HelperClass
from fastapi import HTTPException
from io import BytesIO
import pandas as pd
from sqlalchemy import text

class AccountabilityClass:
    def __init__(self, db):
        self.db = db

    def store(self, branch_office_id, expense_type_id, tax_status_id, period, amount):
        token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
        branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == branch_office_id).first()
        expense_type = self.db.query(ExpenseTypeModel).filter(ExpenseTypeModel.id == expense_type_id).first()
        splitted_period = period.split('-')
        utf8_date = '01-' + splitted_period[1] + '-' + splitted_period[0]

        gloss = (
                branch_office.branch_office
                + "_"
                + expense_type.accounting_account
                + "_"
                + utf8_date
                + "_AsientoLibre"
            )

        if  expense_type.accounting_account != 443000344:
            if tax_status_id == 0:
                data = {
                        "fecha": period + "-01",
                        "glosa": gloss,
                        "detalle": {
                            'debe': {
                                str(expense_type.accounting_account): amount,
                            },
                            'haber': {
                                '111000101': amount,
                            }
                        },
                        "operacion": "I",
                        "documentos": {
                            "emitidos": [
                                {
                                    "dte": '',
                                    "folio": 0,
                                }
                            ]
                        },
                    }
            else:
                data = {
                    "fecha": period + "-01",
                    "glosa": gloss,
                    "detalle": {
                        'debe': {
                            '111000102': amount,
                        },
                        'haber': {
                            str(expense_type.accounting_account): round(amount/1.19),
                            '221000226': round(amount - (amount/1.19)),
                        }
                    },
                    "operacion": "I",
                    "documentos": {
                        "emitidos": [
                            {
                                "dte": '',
                                "folio": 0,
                            }
                        ]
                    },
                }
        else:
            data = {
                "fecha": period + "-01",
                "glosa": gloss,
                "detalle": {
                    'debe': {
                        str(expense_type.accounting_account): amount,
                        '221000223': round((amount/0.8700) - amount),
                    },
                    'haber': {
                        '111000102': round(amount/0.8700),
                    }
                },
                "operacion": "I",
                "documentos": {
                    "emitidos": [
                        {
                            "dte": '',
                            "folio": 0,
                        }
                    ]
                },
            }

        url = f"https://libredte.cl/api/lce/lce_asientos/crear/" + "76063822"

        response = requests.post(
            url,
            json=data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

        print(response.text)

    def delete(self, branch_office_id, period, expense_type_id):
        token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

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
            'Authorization': f'Bearer {token}'
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
            asset_number = entry_id.split("-")[1]
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
                delete_url = f"https://libredte.cl/api/lce/lce_asientos/eliminar/{period_year}/{asset_number}/76063822"
                print(delete_url)

                delete_headers = {
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {token}'
                }

                delete_response = requests.get(delete_url, headers=delete_headers)

                print(delete_response.text)
    
    def store_subscriber_assets(self, branch_office_id, period):
        token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        if branch_office_id == 0:
            branch_offices = self.db.query(BranchOfficeModel).all()

            for branch_office in branch_offices:
                collection_qty = self.db.query(CollectionModel).filter(CollectionModel.branch_office_id == branch_office.id).filter(CollectionModel.added_date == period + "-01").filter(CollectionModel.subscribers > 0).count()

                if collection_qty > 0:
                    collection = self.db.query(CollectionModel).filter(CollectionModel.branch_office_id == branch_office.id).filter(CollectionModel.added_date == period + "-01").filter(CollectionModel.subscribers > 0).first()
              
                    amount = collection.subscribers if collection else 0

                    expense_type = self.db.query(ExpenseTypeModel).filter(ExpenseTypeModel.id == 23).first()
                    splitted_period = period.split('-')
                    utf8_date = '01-' + splitted_period[1] + '-' + splitted_period[0]

                    gloss = (
                            branch_office.branch_office
                            + "_"
                            + expense_type.accounting_account
                            + "_"
                            + utf8_date
                            + "_Abonados"
                        )

                    data = {
                            "fecha": period + "-01",
                            "glosa": gloss,
                            "detalle": {
                                'debe': {
                                    '111000102': amount,
                                },
                                'haber': {
                                    '441000102': round(amount/1.19),
                                    '221000226': round(amount - (amount/1.19)),
                                }
                            },
                            "operacion": "I",
                            "documentos": {
                                "emitidos": [
                                    {
                                        "dte": '',
                                        "folio": 0,
                                    }
                                ]
                            },
                        }


                    url = f"https://libredte.cl/api/lce/lce_asientos/crear/" + "76063822"

                    response = requests.post(
                        url,
                        json=data,
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json",
                        },
                    )

                    print(response.text)
        else:
            branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == branch_office_id).first()
            collection = self.db.query(CollectionModel).filter(CollectionModel.branch_office_id == branch_office_id).filter(CollectionModel.added_date == period + "-01").filter(CollectionModel.subscribers > 0).first()
            collection_qty = self.db.query(CollectionModel).filter(CollectionModel.branch_office_id == branch_office.id).filter(CollectionModel.added_date == period + "-01").filter(CollectionModel.subscribers > 0).count()
            
            if collection_qty > 0:
                expense_type = self.db.query(ExpenseTypeModel).filter(ExpenseTypeModel.id == 23).first()
                splitted_period = period.split('-')
                utf8_date = '01-' + splitted_period[1] + '-' + splitted_period[0]

                gloss = (
                        branch_office.branch_office
                        + "_"
                        + expense_type.accounting_account
                        + "_"
                        + utf8_date
                        + "_Abonados"
                    )

                data = {
                        "fecha": period + "-01",
                        "glosa": gloss,
                        "detalle": {
                            'debe': {
                                '111000102': amount,
                            },
                            'haber': {
                                '441000102': round(amount/1.19),
                                '221000226': round(amount - (amount/1.19)),
                            }
                        },
                        "operacion": "I",
                        "documentos": {
                            "emitidos": [
                                {
                                    "dte": '',
                                    "folio": 0,
                                }
                            ]
                        },
                    }


                url = f"https://libredte.cl/api/lce/lce_asientos/crear/" + "76063822"

                response = requests.post(
                    url,
                    json=data,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )

                print(response.text)

    def delete_subscriber_assets(self, branch_office_id, period):
        token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        if branch_office_id != None and branch_office_id != '' and branch_office_id != 0:
            branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == branch_office_id).first()

            gloss = str(branch_office.branch_office) + "_Abonados"
        else:
            gloss = "Abonados"

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
            "cuenta": None,
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
            'Authorization': f'Bearer {token}'
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
            asset_number = entry_id.split("-")[1]
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

            details = entry.get("detalle", [])
            for item in details:
                # Optional: use 'item' data if needed
                delete_url = f"https://libredte.cl/api/lce/lce_asientos/eliminar/{period_year}/{asset_number}/76063822"
                print(delete_url)

                delete_headers = {
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {token}'
                }

                delete_response = requests.get(delete_url, headers=delete_headers)

                print(delete_response.text)

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

                    branch_office_id = row["branch_office_id"]
                    accounting_account = row["accounting_account"]
                    amount = row["amount"]
                    period = row["period"]
                    tax_status_id = 0

                    branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id==branch_office_id).first()
                    if not branch_office:
                        print(f"[Fila {index + 2}] Sucursal no encontrada")
                        continue

                    expense_type = self.db.query(ExpenseTypeModel).filter(ExpenseTypeModel.accounting_account==accounting_account).first()
                    if not expense_type:
                        print(f"[Fila {index + 2}] Tipo de gasto no encontrado")
                        continue
                    
                    splitted_period = period.split('-')
                    utf8_date = '01-' + splitted_period[1] + '-' + splitted_period[0]

                    gloss = (
                        branch_office.branch_office + "_" +
                        expense_type.accounting_account + "_" +
                        utf8_date + "_AsientoLibre"
                    )

                    if expense_type.accounting_account != 443000344:
                        if tax_status_id == 0:
                            data = {
                                "fecha": period + "-01",
                                "glosa": gloss,
                                "detalle": {
                                    "debe": {str(expense_type.accounting_account): amount},
                                    "haber": {"111000101": amount},
                                },
                                "operacion": "I",
                                "documentos": {"emitidos": [{"dte": '', "folio": 0}]},
                            }
                        else:
                            neto = round(amount / 1.19)
                            iva = round(amount - neto)
                            data = {
                                "fecha": period + "-01",
                                "glosa": gloss,
                                "detalle": {
                                    "debe": {"111000102": amount},
                                    "haber": {
                                        str(expense_type.accounting_account): neto,
                                        "221000226": iva,
                                    },
                                },
                                "operacion": "E",
                                "documentos": {"emitidos": [{"dte": '', "folio": 0}]},
                            }
                    else:
                        base = round(amount / 0.87)
                        iva = base - amount
                        data = {
                            "fecha": period + "-01",
                            "glosa": gloss,
                            "detalle": {
                                "debe": {
                                    str(expense_type.accounting_account): amount,
                                    "221000223": iva,
                                },
                                "haber": {"111000102": base},
                            },
                            "operacion": "I",
                            "documentos": {"emitidos": [{"dte": '', "folio": 0}]},
                        }

                    url = "https://libredte.cl/api/lce/lce_asientos/crear/76063822"
                    response = requests.post(
                        url,
                        json=data,
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json",
                        },
                    )

                    print(response.text)

                except Exception as row_error:
                    print(f"[Fila {index + 2}] Error procesando fila: {row_error}")

            return {"status": "success", "message": "Proceso completado"}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")
