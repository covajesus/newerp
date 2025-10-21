import requests
from app.backend.db.models import BranchOfficeModel, ExpenseTypeModel, CollectionModel
import json
from calendar import monthrange
from app.backend.classes.helper_class import HelperClass
from fastapi import HTTPException
from io import BytesIO
import pandas as pd
from sqlalchemy import text, func, extract
from decimal import Decimal

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
            if tax_status_id == 2:
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
            "glosa": None,
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

            print(entries)
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
              
                    net_amount = collection.subscribers if collection else 0

                    gross_amount = round(net_amount * 1.19)

                    expense_type = self.db.query(ExpenseTypeModel).filter(ExpenseTypeModel.id == 25).first()
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
                                    '111000102': gross_amount,
                                },
                                'haber': {
                                    '441000102': net_amount,
                                    '221000226': (gross_amount - net_amount),
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

                    print(data)


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
                expense_type = self.db.query(ExpenseTypeModel).filter(ExpenseTypeModel.id == 25).first()
                splitted_period = period.split('-')
                utf8_date = '01-' + splitted_period[1] + '-' + splitted_period[0]

                gross_amount = round(net_amount * 1.19)

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
                                    '111000102': gross_amount,
                                },
                                'haber': {
                                    '441000102': net_amount,
                                    '221000226': (gross_amount - net_amount),
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
                
                print(data)


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

    def store_income_assets(self, branch_office_id, period):
        token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        if branch_office_id == 0:
            branch_offices = self.db.query(BranchOfficeModel).all()

            for branch_office in branch_offices:
                collection_qty = self.db.query(CollectionModel).filter(CollectionModel.branch_office_id == branch_office.id).filter(CollectionModel.added_date == period + "-01").filter(CollectionModel.income > 0).count()

                if collection_qty > 0:
                    collection = self.db.query(CollectionModel).filter(CollectionModel.branch_office_id == branch_office.id).filter(CollectionModel.added_date == period + "-01").filter(CollectionModel.income > 0).first()
              
                    amount = collection.income if collection else 0

                    expense_type = self.db.query(ExpenseTypeModel).filter(ExpenseTypeModel.id == 24).first()
                    splitted_period = period.split('-')
                    utf8_date = '01-' + splitted_period[1] + '-' + splitted_period[0]

                    gloss = (
                            branch_office.branch_office
                            + "_"
                            + expense_type.accounting_account
                            + "_"
                            + utf8_date
                            + "_Ingresos"
                        )

                    data = {
                            "fecha": period + "-01",
                            "glosa": gloss,
                            "detalle": {
                                'debe': {
                                    '111000102': amount,
                                },
                                'haber': {
                                    '441000103': round(amount/1.19),
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
            collection = self.db.query(CollectionModel).filter(CollectionModel.branch_office_id == branch_office_id).filter(CollectionModel.added_date == period + "-01").filter(CollectionModel.income > 0).first()
            collection_qty = self.db.query(CollectionModel).filter(CollectionModel.branch_office_id == branch_office.id).filter(CollectionModel.added_date == period + "-01").filter(CollectionModel.income > 0).count()
            
            if collection_qty > 0:
                amount = collection.income if collection else 0

                expense_type = self.db.query(ExpenseTypeModel).filter(ExpenseTypeModel.id == 24).first()
                splitted_period = period.split('-')
                utf8_date = '01-' + splitted_period[1] + '-' + splitted_period[0]

                gloss = (
                        branch_office.branch_office
                        + "_"
                        + expense_type.accounting_account
                        + "_"
                        + utf8_date
                        + "_Ingresos"
                    )

                data = {
                        "fecha": period + "-01",
                        "glosa": gloss,
                        "detalle": {
                            'debe': {
                                '111000102': amount,
                            },
                            'haber': {
                                '441000103': round(amount/1.19),
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

    def delete_income_assets(self, branch_office_id, period):
        token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        if branch_office_id != None and branch_office_id != '' and branch_office_id != 0:
            branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == branch_office_id).first()

            gloss = str(branch_office.branch_office) + "_Ingresos"
        else:
            gloss = "Ingresos"

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
            "haber_hasta": None,
            "email": None,
            "documento": None,
            "documento_razon_social": None,
            "documento_folio": None,
            "solo_tipos_dte": None,
            "solo_tipos_operacion": None,
            "p": 0,
            "d": "FEC",
            "h": "D",
            "total": True,
        }

        response = requests.get(
            url,
            params=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

        assets = json.loads(response.text)

        for asset in assets:
            if "Ingresos" in asset["glosa"]:
                delete_response = requests.get(
                    f"https://libredte.cl/api/lce/lce_asientos/eliminar/{asset['codigo']}/76063822",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )

                print(delete_response.text)

    def get_monthly_collections_data(self, period=None):
        """
        Obtiene datos de collections agrupados por sucursal y mes usando SQLAlchemy
        """
        # Construir la consulta base con SQLAlchemy
        query = self.db.query(
            CollectionModel.branch_office_id,
            (func.ifnull(func.sum(CollectionModel.cash_net_amount), 0) + 
             func.ifnull(func.sum(CollectionModel.card_net_amount), 0)).label('ingresos'),
            func.ifnull(func.sum(CollectionModel.subscribers), 0).label('subscribers_total'),
            extract('year', CollectionModel.added_date).label('year'),
            extract('month', CollectionModel.added_date).label('month')
        )
        
        # Si se especifica un período, filtrar por año-mes
        if period:
            year, month = period.split('-')
            query = query.filter(
                extract('year', CollectionModel.added_date) == int(year),
                extract('month', CollectionModel.added_date) == int(month)
            )
        
        # Agrupar por sucursal y fecha
        query = query.group_by(
            CollectionModel.branch_office_id,
            extract('year', CollectionModel.added_date),
            extract('month', CollectionModel.added_date)
        )
        
        return query.all()

    def store_branch_office_incomes(self, period):
        """
        Procesa los ingresos por sucursal para un período específico
        Crea asientos contables con:
        - Banco (111000102) en el debe
        - Ingresos por venta (441000101) en el haber 
        - IVA débito fiscal (221000226) en el haber
        """
        token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
        
        # Obtener datos de collections para el período
        collections_data = self.get_monthly_collections_data(period)
        
        results = []
        
        for row in collections_data:
            branch_office_id = row.branch_office_id
            gross_incomes = row.ingresos * 1.19
            subscribers_total = row.subscribers_total
            year = row.year
            month = row.month
            
            # Obtener información de la sucursal
            branch_office = self.db.query(BranchOfficeModel).filter(
                BranchOfficeModel.id == branch_office_id
            ).first()
            
            if not branch_office or gross_incomes <= 0:
                continue
                
            # Calcular montos
            net_incomes = round(gross_incomes)  # Monto sin IVA
            iva_amount = gross_incomes - net_incomes   # IVA
            
            # Crear fecha en formato correcto
            splitted_period = period.split('-')
            utf8_date = '01-' + splitted_period[1] + '-' + splitted_period[0]
            
            # Crear glosa siguiendo el formato especificado
            gloss = (
                branch_office.branch_office
                + "_441000101_"
                + utf8_date
                + "_BoletaFiscal"
            )
            
            # Estructura del asiento contable
            data = {
                "fecha": period + "-01",
                "glosa": gloss,
                "detalle": {
                    'debe': {
                        '111000102': gross_incomes,  # Banco
                    },
                    'haber': {
                        '441000101': net_incomes,     # Ingresos por venta
                        '221000226': iva_amount,       # IVA débito fiscal
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
            
            # Enviar asiento a LibreDTE
            url = f"https://libredte.cl/api/lce/lce_asientos/crear/76063822"
            
            try:
                response = requests.post(
                    url,
                    json=data,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )
                
                result_data = {
                    "branch_office_id": branch_office_id,
                    "branch_office_name": branch_office.branch_office,
                    "period": period,
                    "ingresos_brutos": gross_incomes,
                    "ingreso_neto": net_incomes,
                    "iva_amount": iva_amount,
                    "subscribers_total": subscribers_total,
                    "gloss": gloss,
                    "response_status": response.status_code,
                    "response_text": response.text
                }
                
                results.append(result_data)
                print(f"✅ Asiento creado para {branch_office.branch_office}: {response.text}")
                
            except Exception as e:
                error_data = {
                    "branch_office_id": branch_office_id,
                    "branch_office_name": branch_office.branch_office,
                    "period": period,
                    "error": str(e)
                }
                results.append(error_data)
                print(f"❌ Error creando asiento para {branch_office.branch_office}: {str(e)}")
        
        return results

    def delete_income_assets(self, period):
        """
        Elimina asientos de ingresos para un período específico
        """
        token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        response = requests.get(
            "https://libredte.cl/api/lce/lce_asientos/buscar/76063822",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

        assets = json.loads(response.text)

        for asset in assets:
            if "BoletaFiscal" in asset["glosa"] and period in asset["fecha"]:
                delete_response = requests.get(
                    f"https://libredte.cl/api/lce/lce_asientos/eliminar/{asset['codigo']}/76063822",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )

                print(delete_response.text)

    def store_all_assets(self, period):
        """
        Procesa TODOS los activos para un período específico:
        1. Elimina asientos existentes (ingresos y abonados)
        2. Carga asientos de ingresos por ventas
        3. Carga asientos de abonados
        """
        token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
        
        results = {
            "period": period,
            "eliminated_income_assets": [],
            "eliminated_subscriber_assets": [],
            "created_income_assets": [],
            "created_subscriber_assets": [],
            "errors": []
        }
        
        try:
            print(f"🚀 Iniciando procesamiento completo de activos para período: {period}")
            
            # PASO 1: Eliminar asientos existentes de ingresos (BoletaFiscal)
            print("🗑️ Eliminando asientos de ingresos existentes...")
            
            # Buscar asientos con parámetros específicos para el período
            search_params = {
                "cuenta": None,
                "debe": None,
                "debe_desde": None,
                "debe_hasta": None,
                "fecha_desde": f"{period}-01",
                "fecha_hasta": f"{period}-31",
                "glosa": "BoletaFiscal",
                "haber": None,
                "haber_desde": None,
                "haber_hasta": None,
                "operacion": None,
                "periodo": int(period.split('-')[0])  # Solo el año
            }
            
            print(f"🔍 Parámetros de búsqueda: {search_params}")
            
            response = requests.post(  # Cambiar a POST para enviar parámetros
                "https://libredte.cl/api/lce/lce_asientos/buscar/76063822",
                json=search_params,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            
            print(f"📡 Respuesta de LibreDTE: {response.status_code}")
            print(f"📄 Contenido completo: {response.text}")  # Ver contenido completo para debug
            
            try:
                response_data = json.loads(response.text)
                print(f"🔍 Tipo de respuesta: {type(response_data)}")
                print(f"📋 Respuesta parseada: {response_data}")
                
                # Verificar si la respuesta es una lista
                if isinstance(response_data, list):
                    assets = response_data
                elif isinstance(response_data, dict):
                    # Si es un diccionario, puede tener una estructura diferente
                    if 'asientos' in response_data:
                        assets = response_data['asientos']
                    elif 'data' in response_data:
                        assets = response_data['data']
                    else:
                        print("⚠️ Respuesta de LibreDTE no contiene assets en formato esperado")
                        print(f"🔑 Keys disponibles: {list(response_data.keys()) if isinstance(response_data, dict) else 'No es dict'}")
                        assets = []
                elif isinstance(response_data, str):
                    print("⚠️ Respuesta es un string, posiblemente un mensaje de error")
                    print(f"📝 Mensaje: {response_data}")
                    assets = []
                else:
                    print(f"⚠️ Respuesta de LibreDTE no es una lista ni diccionario válido. Tipo: {type(response_data)}")
                    assets = []
                    
            except json.JSONDecodeError as e:
                print(f"❌ Error al parsear JSON de LibreDTE: {str(e)}")
                print(f"📄 Respuesta raw: {response.text}")
                assets = []
            
            print(f"📊 Total de assets encontrados: {len(assets)}")
            
            for asset in assets:
                if isinstance(asset, dict) and "glosa" in asset and "fecha" in asset:
                    print(f"🔍 Revisando asset: {asset.get('asiento', 'N/A')} - {asset.get('glosa', 'N/A')} - {asset.get('fecha', 'N/A')}")
                    
                    # Verificar criterios de eliminación para BoletaFiscal
                    has_boleta_fiscal = "BoletaFiscal" in asset["glosa"]
                    has_period = period in asset["fecha"]
                    
                    print(f"   📋 BoletaFiscal en glosa: {has_boleta_fiscal}")
                    print(f"   📅 Período {period} en fecha: {has_period}")
                    
                    if has_boleta_fiscal and has_period:
                        # Verificar si el asset tiene el campo 'asiento' antes de intentar eliminarlo
                        if 'asiento' not in asset:
                            print(f"⚠️ Asset no tiene campo 'asiento', saltando eliminación: {asset}")
                            results["errors"].append({
                                "type": "missing_asiento_field",
                                "error": "Asset sin campo 'asiento'",
                                "asset": asset
                            })
                            continue
                            
                        try:
                            codigo_asset = asset['asiento']  # Usar 'asiento' en lugar de 'codigo'
                            print(f"🗑️ Intentando eliminar asset de ingresos: {codigo_asset}")
                            
                            # Usar directamente el formato que funciona: año/asiento/contribuyente
                            year = period.split('-')[0]  # Extraer año del período (ej: "2025-08" -> "2025")
                            delete_url = f"https://libredte.cl/api/lce/lce_asientos/eliminar/{year}/{codigo_asset}/76063822"
                            print(f"🔗 URL de eliminación: {delete_url}")
                            
                            delete_response = requests.get(
                                delete_url,
                                headers={
                                    "Authorization": f"Bearer {token}",
                                    "Content-Type": "application/json",
                                },
                            )
                            print(f"📡 Respuesta eliminación: {delete_response.status_code} - {delete_response.text}")
                            
                            # Si el primer formato falla, probar formato alternativo
                            if delete_response.status_code != 200:
                                print(f"❌ Primer formato falló, probando formato alternativo...")
                                # Probar con el año completo
                                delete_url_alt = f"https://libredte.cl/api/lce/lce_asientos/eliminar/2025/{codigo_asset}/76063822"
                                print(f"🔗 URL alternativa: {delete_url_alt}")
                                
                                delete_response_alt = requests.get(
                                    delete_url_alt,
                                    headers={
                                        "Authorization": f"Bearer {token}",
                                        "Content-Type": "application/json",
                                    },
                                )
                                print(f"� Respuesta alternativa: {delete_response_alt.status_code} - {delete_response_alt.text}")
                                
                                # Si tampoco funciona, probar con el ID completo
                                if delete_response_alt.status_code != 200 and 'id' in asiento:
                                    print(f"❌ Formato alternativo falló, probando con ID completo...")
                                    asset_id = asset['id']  # '2025-28435'
                                    delete_url_id = f"https://libredte.cl/api/lce/lce_asientos/eliminar/{asset_id}/76063822"
                                    print(f"🔗 URL con ID: {delete_url_id}")
                                    
                                    delete_response_id = requests.get(
                                        delete_url_id,
                                        headers={
                                            "Authorization": f"Bearer {token}",
                                            "Content-Type": "application/json",
                                        },
                                    )
                                    print(f"📡 Respuesta con ID: {delete_response_id.status_code} - {delete_response_id.text}")
                                    delete_response = delete_response_id  # Usar esta respuesta para el logging
                                else:
                                    delete_response = delete_response_alt
                            
                            results["eliminated_income_assets"].append({
                                "codigo": codigo_asset,
                                "glosa": asiento.get("glosa", 'N/A'),
                                "delete_status": delete_response.status_code,
                                "response": delete_response.text
                            })
                            
                            if delete_response.status_code == 200:
                                print(f"🔍 Eliminado asset de ingresos: {codigo_asset}")
                            else:
                                print(f"❌ No se pudo eliminar asset: {codigo_asset} - Status: {delete_response.status_code}")
                                
                        except Exception as e:
                            print(f"❌ Error eliminando asiento de ingresos: {str(e)}")
                            results["errors"].append({
                                "type": "delete_income_asset",
                                "error": str(e),
                                "asset": asset
                            })
                    else:
                        print(f"⏭️ Asset no cumple criterios para eliminación")
                else:
                    print(f"⚠️ Asset no tiene estructura válida: {asset}")
            
            # PASO 2: Eliminar asientos existentes de abonados
            print("🗑️ Eliminando asientos de abonados existentes...")
            
            # Buscar asientos de abonados con parámetros específicos
            search_params_abonados = {
                "cuenta": None,
                "debe": None,
                "debe_desde": None,
                "debe_hasta": None,
                "fecha_desde": f"{period}-01",
                "fecha_hasta": f"{period}-31",
                "glosa": "Abonados",
                "haber": None,
                "haber_desde": None,
                "haber_hasta": None,
                "operacion": None,
                "periodo": int(period.split('-')[0])  # Solo el año
            }
            
            print(f"🔍 Parámetros de búsqueda abonados: {search_params_abonados}")
            
            response_abonados = requests.post(
                "https://libredte.cl/api/lce/lce_asientos/buscar/76063822",
                json=search_params_abonados,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            
            print(f"📡 Respuesta búsqueda abonados: {response_abonados.status_code}")
            print(f"📄 Contenido abonados: {response_abonados.text}")
            
            try:
                asientos_abonados = json.loads(response_abonados.text)
                if isinstance(asientos_abonados, list):
                    asientos_abonados_list = asientos_abonados
                elif isinstance(asientos_abonados, dict) and 'data' in asientos_abonados:
                    asientos_abonados_list = asientos_abonados['data']
                else:
                    asientos_abonados_list = []
            except:
                asientos_abonados_list = []
            
            print(f"📊 Total de asientos de abonados encontrados: {len(asientos_abonados_list)}")
            
            for asiento in asientos_abonados_list:
                if isinstance(asiento, dict) and "glosa" in asiento and "fecha" in asiento:
                    print(f"🔍 Revisando asiento: {asiento.get('asiento', 'N/A')} - {asiento.get('glosa', 'N/A')} - {asiento.get('fecha', 'N/A')}")
                    
                    # Verificar criterios de eliminación para Abonados
                    has_abonados = "Abonados" in asiento["glosa"]
                    has_period = period in asiento["fecha"]
                    
                    print(f"   👥 Abonados en glosa: {has_abonados}")
                    print(f"   📅 Período {period} en fecha: {has_period}")
                    
                    if has_abonados and has_period:
                        # Verificar si el asiento tiene el campo 'asiento' antes de intentar eliminarlo
                        if 'asiento' not in asiento:
                            print(f"⚠️ Asiento no tiene campo 'asiento', saltando eliminación: {asiento}")
                            results["errors"].append({
                                "type": "missing_asiento_field",
                                "error": "Asiento sin campo 'asiento'",
                                "asiento": asiento
                            })
                            continue
                            
                        try:
                            codigo_asiento = asiento['asiento']  # Usar 'asiento' en lugar de 'codigo'
                            print(f"🗑️ Intentando eliminar asiento de abonados: {codigo_asiento}")
                            
                            # Usar directamente el formato que funciona: año/asiento/contribuyente
                            year = period.split('-')[0]  # Extraer año del período (ej: "2025-08" -> "2025")
                            delete_url = f"https://libredte.cl/api/lce/lce_asientos/eliminar/{year}/{codigo_asiento}/76063822"
                            print(f"🔗 URL de eliminación: {delete_url}")
                            
                            delete_response = requests.get(
                                delete_url,
                                headers={
                                    "Authorization": f"Bearer {token}",
                                    "Content-Type": "application/json",
                                },
                            )
                            print(f"📡 Respuesta eliminación: {delete_response.status_code} - {delete_response.text}")
                            
                            # Si el primer formato falla, probar formato alternativo
                            if delete_response.status_code != 200:
                                print(f"❌ Primer formato falló, probando formato alternativo...")
                                # Probar con el año completo
                                delete_url_alt = f"https://libredte.cl/api/lce/lce_asientos/eliminar/2025/{codigo_asiento}/76063822"
                                print(f"🔗 URL alternativa: {delete_url_alt}")
                                
                                delete_response_alt = requests.get(
                                    delete_url_alt,
                                    headers={
                                        "Authorization": f"Bearer {token}",
                                        "Content-Type": "application/json",
                                    },
                                )
                                print(f"� Respuesta alternativa: {delete_response_alt.status_code} - {delete_response_alt.text}")
                                
                                # Si tampoco funciona, probar con el ID completo
                                if delete_response_alt.status_code != 200 and 'id' in asiento:
                                    print(f"❌ Formato alternativo falló, probando con ID completo...")
                                    asiento_id = asiento['id']  # '2025-28435'
                                    delete_url_id = f"https://libredte.cl/api/lce/lce_asientos/eliminar/{asiento_id}/76063822"
                                    print(f"🔗 URL con ID: {delete_url_id}")
                                    
                                    delete_response_id = requests.get(
                                        delete_url_id,
                                        headers={
                                            "Authorization": f"Bearer {token}",
                                            "Content-Type": "application/json",
                                        },
                                    )
                                    print(f"📡 Respuesta con ID: {delete_response_id.status_code} - {delete_response_id.text}")
                                    delete_response = delete_response_id  # Usar esta respuesta para el logging
                                else:
                                    delete_response = delete_response_alt
                            
                            results["eliminated_subscriber_assets"].append({
                                "codigo": codigo_asiento,
                                "glosa": asiento.get("glosa", 'N/A'),
                                "delete_status": delete_response.status_code,
                                "response": delete_response.text
                            })
                            
                            if delete_response.status_code == 200:
                                print(f"✅ Eliminado asiento de abonados: {codigo_asiento}")
                            else:
                                print(f"❌ No se pudo eliminar asiento: {codigo_asiento} - Status: {delete_response.status_code}")
                                
                        except Exception as e:
                            print(f"❌ Error eliminando asiento de abonados: {str(e)}")
                            results["errors"].append({
                                "type": "delete_subscriber_asset",
                                "error": str(e),
                                "asiento": asiento
                            })
                    else:
                        print(f"⏭️ Asiento no cumple criterios para eliminación")
                else:
                    print(f"⚠️ Asiento no tiene estructura válida: {asiento}")
            
            # PASO 3: Crear asientos de ingresos por ventas
            print("💰 Creando asientos de ingresos por ventas...")
            collections_data = self.get_monthly_collections_data(period)
            
            for row in collections_data:
                branch_office_id = row.branch_office_id
                gross_incomes = float(row.ingresos) * 1.19

                if gross_incomes <= 0:
                    continue
                
                branch_office = self.db.query(BranchOfficeModel).filter(
                    BranchOfficeModel.id == branch_office_id
                ).first()
                
                if not branch_office:
                    continue
                
                # Calcular montos para ingresos
                gross_incomes = float(gross_incomes)  # Convertir Decimal a float
                net_incomes = round(gross_incomes / 1.19)
                iva_amount = gross_incomes - net_incomes

                splitted_period = period.split('-')
                utf8_date = '01-' + splitted_period[1] + '-' + splitted_period[0]
                
                gloss = (
                    branch_office.branch_office
                    + "_441000101_"
                    + utf8_date
                    + "_BoletaFiscal"
                )
                
                data = {
                    "fecha": period + "-01",
                    "glosa": gloss,
                    "detalle": {
                        'debe': {
                            '111000102': gross_incomes,
                        },
                        'haber': {
                            '441000101': net_incomes,
                            '221000226': iva_amount,
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
                
                try:
                    response = requests.post(
                        f"https://libredte.cl/api/lce/lce_asientos/crear/76063822",
                        json=data,
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json",
                        },
                    )
                    
                    results["created_income_assets"].append({
                        "branch_office_id": branch_office_id,
                        "branch_office_name": branch_office.branch_office,
                        "ingresos_brutos": gross_incomes,
                        "ingreso_neto": net_incomes,
                        "iva_amount": iva_amount,
                        "gloss": gloss,
                        "response_status": response.status_code,
                        "response_text": response.text
                    })
                    print(f"✅ Asiento de ingresos creado para {branch_office.branch_office}")
                    
                except Exception as e:
                    results["errors"].append({
                        "type": "income_asset",
                        "branch_office_id": branch_office_id,
                        "error": str(e)
                    })
                    print(f"❌ Error creando asiento de ingresos para {branch_office.branch_office}: {str(e)}")
            
            # PASO 4: Crear asientos de abonados
            print("👥 Creando asientos de abonados...")
            branch_offices = self.db.query(BranchOfficeModel).all()
            
            for branch_office in branch_offices:
                collection_qty = self.db.query(CollectionModel).filter(
                    CollectionModel.branch_office_id == branch_office.id
                ).filter(
                    CollectionModel.added_date == period + "-01"
                ).filter(
                    CollectionModel.subscribers > 0
                ).count()
                
                if collection_qty > 0:
                    collection = self.db.query(CollectionModel).filter(
                        CollectionModel.branch_office_id == branch_office.id
                    ).filter(
                        CollectionModel.added_date == period + "-01"
                    ).filter(
                        CollectionModel.subscribers > 0
                    ).first()
                    
                    amount = collection.subscribers if collection else 0
                    
                    if amount <= 0:
                        continue
                    
                    # Convertir amount a float para evitar problemas con Decimal
                    amount = float(amount)

                    gross_amount = round(amount * 1.19)
                    
                    expense_type = self.db.query(ExpenseTypeModel).filter(ExpenseTypeModel.id == 25).first()
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
                                '111000102': gross_amount,
                            },
                            'haber': {
                                '441000102': amount,
                                '221000226': (gross_amount - amount),
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
                    
                    try:
                        response = requests.post(
                            f"https://libredte.cl/api/lce/lce_asientos/crear/76063822",
                            json=data,
                            headers={
                                "Authorization": f"Bearer {token}",
                                "Content-Type": "application/json",
                            },
                        )
                        
                        results["created_subscriber_assets"].append({
                            "branch_office_id": branch_office.id,
                            "branch_office_name": branch_office.branch_office,
                            "subscribers": amount,
                            "neto": round(amount/1.19),
                            "iva": round(amount - (amount/1.19)),
                            "gloss": gloss,
                            "response_status": response.status_code,
                            "response_text": response.text
                        })
                        print(f"✅ Asiento de abonados creado para {branch_office.branch_office}")
                        
                    except Exception as e:
                        results["errors"].append({
                            "type": "subscriber_asset",
                            "branch_office_id": branch_office.id,
                            "error": str(e)
                        })
                        print(f"❌ Error creando asiento de abonados para {branch_office.branch_office}: {str(e)}")
            
            # PASO 4: Verificación final - ¿Se eliminaron realmente los asientos?
            print("🔍 Verificación final: comprobando si los asientos fueron eliminados...")
            
            # Verificar asientos de ingresos (BoletaFiscal)
            try:
                search_params_verificacion = {
                    "cuenta": None,
                    "debe": None,
                    "debe_desde": None,
                    "debe_hasta": None,
                    "fecha_desde": f"{period}-01",
                    "fecha_hasta": f"{period}-31",
                    "glosa": "BoletaFiscal",
                    "haber": None,
                    "haber_desde": None,
                    "haber_hasta": None,
                    "operacion": None,
                    "periodo": int(period.split('-')[0])
                }
                
                response_verificacion = requests.post(
                    "https://libredte.cl/api/lce/lce_asientos/buscar/76063822",
                    json=search_params_verificacion,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )
                
                if response_verificacion.status_code == 200:
                    try:
                        asientos_restantes = json.loads(response_verificacion.text)
                        if isinstance(asientos_restantes, list):
                            asientos_boleta_restantes = [a for a in asientos_restantes if isinstance(a, dict) and "BoletaFiscal" in a.get("glosa", "")]
                        else:
                            asientos_boleta_restantes = []
                        
                        print(f"📊 Asientos BoletaFiscal restantes después de eliminación: {len(asientos_boleta_restantes)}")
                        if len(asientos_boleta_restantes) > 0:
                            print(f"⚠️ ADVERTENCIA: Aún quedan {len(asientos_boleta_restantes)} asientos BoletaFiscal sin eliminar")
                            for asiento in asientos_boleta_restantes[:3]:  # Mostrar solo los primeros 3
                                print(f"   • {asiento.get('asiento', 'N/A')}: {asiento.get('glosa', 'N/A')}")
                        else:
                            print(f"✅ Todos los asientos BoletaFiscal fueron eliminados correctamente")
                    except:
                        print(f"❌ Error al verificar asientos BoletaFiscal restantes")
                        
            except Exception as e:
                print(f"❌ Error en verificación de asientos BoletaFiscal: {str(e)}")
            
            # Verificar asientos de abonados
            try:
                search_params_abonados_verificacion = {
                    "cuenta": None,
                    "debe": None,
                    "debe_desde": None,
                    "debe_hasta": None,
                    "fecha_desde": f"{period}-01",
                    "fecha_hasta": f"{period}-31",
                    "glosa": "Abonados",
                    "haber": None,
                    "haber_desde": None,
                    "haber_hasta": None,
                    "operacion": None,
                    "periodo": int(period.split('-')[0])
                }
                
                response_abonados_verificacion = requests.post(
                    "https://libredte.cl/api/lce/lce_asientos/buscar/76063822",
                    json=search_params_abonados_verificacion,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )
                
                if response_abonados_verificacion.status_code == 200:
                    try:
                        asientos_abonados_restantes_raw = json.loads(response_abonados_verificacion.text)
                        if isinstance(asientos_abonados_restantes_raw, list):
                            asientos_abonados_restantes = [a for a in asientos_abonados_restantes_raw if isinstance(a, dict) and "Abonados" in a.get("glosa", "")]
                        else:
                            asientos_abonados_restantes = []
                        
                        print(f"📊 Asientos Abonados restantes después de eliminación: {len(asientos_abonados_restantes)}")
                        if len(asientos_abonados_restantes) > 0:
                            print(f"⚠️ ADVERTENCIA: Aún quedan {len(asientos_abonados_restantes)} asientos Abonados sin eliminar")
                            for asiento in asientos_abonados_restantes[:3]:  # Mostrar solo los primeros 3
                                print(f"   • {asiento.get('asiento', 'N/A')}: {asiento.get('glosa', 'N/A')}")
                        else:
                            print(f"✅ Todos los asientos Abonados fueron eliminados correctamente")
                    except:
                        print(f"❌ Error al verificar asientos Abonados restantes")
                        
            except Exception as e:
                print(f"❌ Error en verificación de asientos Abonados: {str(e)}")
            
            print(f"🎉 Procesamiento completo finalizado para período: {period}")
            return results
            
        except Exception as e:
            results["errors"].append({
                "type": "general",
                "error": str(e)
            })
            print(f"❌ Error general en procesamiento: {str(e)}")
            return results

    def debug_libredte_structure(self, period="2025-08"):
        """
        Método de debug para entender la estructura de respuesta de LibreDTE
        """
        token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
        
        print(f"🔍 DEBUG: Analizando estructura de LibreDTE para período {period}")
        
        # Parámetros de búsqueda básicos
        search_params = {
            "cuenta": None,
            "debe": None,
            "debe_desde": None,
            "debe_hasta": None,
            "fecha_desde": f"{period}-01",
            "fecha_hasta": f"{period}-31",
            "glosa": None,  # Sin filtro de glosa para obtener todos
            "haber": None,
            "haber_desde": None,
            "haber_hasta": None,
            "operacion": None,
            "periodo": int(period.split('-')[0])
        }
        
        print(f"📋 Parámetros de búsqueda: {search_params}")
        
        try:
            response = requests.post(
                "https://libredte.cl/api/lce/lce_asientos/buscar/76063822",
                json=search_params,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            
            print(f"📡 Status Code: {response.status_code}")
            print(f"📄 Response Headers: {dict(response.headers)}")
            print(f"📄 Response Text (primeros 1000 chars): {response.text[:1000]}")
            
            if response.status_code == 200:
                try:
                    data = json.loads(response.text)
                    print(f"🔍 Tipo de respuesta: {type(data)}")
                    
                    if isinstance(data, list):
                        print(f"📋 Es una lista con {len(data)} elementos")
                        if len(data) > 0:
                            print(f"🔍 Primer elemento: {data[0]}")
                            print(f"🔑 Keys del primer elemento: {list(data[0].keys()) if isinstance(data[0], dict) else 'No es dict'}")
                    elif isinstance(data, dict):
                        print(f"📋 Es un diccionario con keys: {list(data.keys())}")
                        # Buscar donde pueden estar los asientos
                        for key, value in data.items():
                            if isinstance(value, list):
                                print(f"🔍 Key '{key}' contiene lista con {len(value)} elementos")
                                if len(value) > 0 and isinstance(value[0], dict):
                                    print(f"🔑 Primer elemento de '{key}' tiene keys: {list(value[0].keys())}")
                    else:
                        print(f"⚠️ Tipo inesperado: {type(data)}")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Error parseando JSON: {str(e)}")
                    
            else:
                print(f"❌ Error en respuesta: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error en debug: {str(e)}")
            
        return {"status": "debug_completed"}

    def test_libredte_response(self):
        """
        Método de prueba para ver exactamente qué devuelve LibreDTE
        """
        token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
        
        print("🧪 PRUEBA: Consultando asientos en LibreDTE...")
        
        # Probar con parámetros específicos
        search_params = {
            "cuenta": None,
            "debe": None,
            "debe_desde": None,
            "debe_hasta": None,
            "fecha_desde": "2025-08-01",
            "fecha_hasta": "2025-08-31", 
            "glosa": "BoletaFiscal",
            "haber": None,
            "haber_desde": None,
            "haber_hasta": None,
            "operacion": None,
            "periodo": 2025
        }
        
        print(f"📋 Parámetros de búsqueda: {search_params}")
        
        response = requests.post(
            "https://libredte.cl/api/lce/lce_asientos/buscar/76063822",
            json=search_params,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        print(f"📄 Raw Response: {response.text}")
        
        if response.status_code == 200:
            try:
                data = json.loads(response.text)
                print(f"🔍 Tipo de datos: {type(data)}")
                print(f"📊 Cantidad de elementos: {len(data) if isinstance(data, (list, dict)) else 'N/A'}")
                
                if isinstance(data, list):
                    print("📋 Es una lista de asientos:")
                    for i, asiento in enumerate(data[:3]):  # Solo mostrar primeros 3
                        print(f"   [{i}] {asiento}")
                elif isinstance(data, dict):
                    print("📋 Es un diccionario:")
                    print(f"   Keys: {list(data.keys())}")
                    print(f"   Contenido: {data}")
                        
            except json.JSONDecodeError as e:
                print(f"❌ Error parseando JSON: {e}")
        else:
            print(f"❌ Error en respuesta: {response.status_code}")
            
        return {
            "status_code": response.status_code,
            "raw_response": response.text,
            "headers": dict(response.headers)
        }

    def delete_seats_by_period(self, period):
        """
        Elimina asientos contables que contengan NotaCredito, Factura o BoletaElectronica 
        para un período específico
        """
        token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
        
        # Lista de términos a buscar en las glosas
        search_terms = ["NotaCredito", "Factura", "BoletaElectronica"]
        
        results = {
            "period": period,
            "eliminated_seats": [],
            "errors": []
        }
        
        try:
            print(f"🗑️ Iniciando eliminación de asientos para período: {period}")
            print(f"🔍 Buscando asientos con términos: {search_terms}")
            
            # Para cada término, buscar y eliminar asientos
            for term in search_terms:
                print(f"\n📋 Procesando término: {term}")
                
                # Parámetros de búsqueda
                search_params = {
                    "cuenta": None,
                    "debe": None,
                    "debe_desde": None,
                    "debe_hasta": None,
                    "fecha_desde": f"{period}-01",
                    "fecha_hasta": f"{period}-31",
                    "glosa": term,
                    "haber": None,
                    "haber_desde": None,
                    "haber_hasta": None,
                    "operacion": None,
                    "periodo": int(period.split('-')[0])  # Solo el año
                }
                
                print(f"🔍 Parámetros de búsqueda para {term}: {search_params}")
                
                # Buscar asientos en LibreDTE
                response = requests.post(
                    "https://libredte.cl/api/lce/lce_asientos/buscar/76063822",
                    json=search_params,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )
                
                print(f"📡 Respuesta búsqueda {term}: {response.status_code}")
                print(f"📄 Contenido: {response.text}")
                
                # Procesar respuesta de búsqueda
                try:
                    assets = json.loads(response.text)
                    if isinstance(assets, list):
                        assets_list = assets
                    elif isinstance(assets, dict) and 'data' in assets:
                        assets_list = assets['data']
                    else:
                        assets_list = []
                except json.JSONDecodeError:
                    assets_list = []
                
                print(f"📊 Total de assets {term} encontrados: {len(assets_list)}")
                
                # Eliminar cada asset encontrado
                for asset in assets_list:
                    if isinstance(asset, dict) and "glosa" in asset and "fecha" in asset:
                        print(f"🔍 Revisando asset: {asset.get('asiento', 'N/A')} - {asset.get('glosa', 'N/A')} - {asset.get('fecha', 'N/A')}")
                        
                        # Verificar criterios de eliminación
                        has_term = term in asset["glosa"]
                        has_period = period in asset["fecha"]
                        
                        print(f"   📋 {term} en glosa: {has_term}")
                        print(f"   📅 Período {period} en fecha: {has_period}")
                        
                        if has_term and has_period:
                            # Verificar si el asset tiene el campo 'asiento'
                            if 'asiento' not in asset:
                                print(f"⚠️ Asset no tiene campo 'asiento', saltando eliminación: {asset}")
                                results["errors"].append({
                                    "type": "missing_asiento_field",
                                    "term": term,
                                    "error": "Asset sin campo 'asiento'",
                                    "asset": asset
                                })
                                continue
                                
                            try:
                                codigo_asset = asset['asiento']
                                print(f"🗑️ Intentando eliminar asset {term}: {codigo_asset}")
                                
                                # Usar formato año/asiento/contribuyente
                                year = period.split('-')[0]
                                delete_url = f"https://libredte.cl/api/lce/lce_asientos/eliminar/{year}/{codigo_asset}/76063822"
                                print(f"🔗 URL de eliminación: {delete_url}")
                                
                                delete_response = requests.get(
                                    delete_url,
                                    headers={
                                        "Authorization": f"Bearer {token}",
                                        "Content-Type": "application/json",
                                    },
                                )
                                print(f"📡 Respuesta eliminación: {delete_response.status_code} - {delete_response.text}")
                                
                                results["eliminated_seats"].append({
                                    "term": term,
                                    "codigo": codigo_asset,
                                    "glosa": asset.get("glosa", 'N/A'),
                                    "fecha": asset.get("fecha", 'N/A'),
                                    "delete_status": delete_response.status_code,
                                    "response": delete_response.text
                                })
                                
                                if delete_response.status_code == 200:
                                    print(f"✅ Eliminado asset {term}: {codigo_asset}")
                                else:
                                    print(f"❌ No se pudo eliminar asset: {codigo_asset} - Status: {delete_response.status_code}")
                                    
                            except Exception as e:
                                print(f"❌ Error eliminando asset {term}: {str(e)}")
                                results["errors"].append({
                                    "type": "delete_error",
                                    "term": term,
                                    "error": str(e),
                                    "asset": asset
                                })
                        else:
                            print(f"⏭️ Asset no cumple criterios para eliminación")
                    else:
                        print(f"⚠️ Asset no tiene estructura válida: {asset}")
            
            print(f"🧹 Eliminación completada para período {period}")
            print(f"📊 Total asientos eliminados: {len(results['eliminated_seats'])}")
            print(f"❌ Total errores: {len(results['errors'])}")
            
            # Resumen por término
            summary_by_term = {}
            for seat in results["eliminated_seats"]:
                term = seat["term"]
                if term not in summary_by_term:
                    summary_by_term[term] = 0
                summary_by_term[term] += 1
            
            results["summary"] = {
                "total_eliminated": len(results["eliminated_seats"]),
                "total_errors": len(results["errors"]),
                "by_term": summary_by_term
            }
            
            return results
            
        except Exception as e:
            print(f"❌ Error general en eliminación: {str(e)}")
            results["errors"].append({
                "type": "general_error",
                "error": str(e)
            })
            return results