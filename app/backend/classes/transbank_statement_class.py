from datetime import datetime
from sqlalchemy.orm import Session
from app.backend.db.models import TransbankStatementModel, BranchOfficesTransbankStatementsModel, BranchOfficeModel, TransbankTotalModel, CollectionModel, CashierModel
from app.backend.classes.helper_class import HelperClass
from fastapi import HTTPException
from sqlalchemy import text
import requests
from io import StringIO
import pandas as pd
import re

class TransbankStatementClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, page=1, items_per_page=10):
        try:
            if page != 0:
                data_query = (
                    self.db.query(
                        TransbankStatementModel.id,
                        TransbankStatementModel.branch_office_id,
                        TransbankStatementModel.original_date,
                        TransbankStatementModel.code,
                        TransbankStatementModel.branch_office_name,
                        TransbankStatementModel.sale_type,
                        TransbankStatementModel.payment_type,
                        TransbankStatementModel.card_number,
                        TransbankStatementModel.sale_description,
                        TransbankStatementModel.amount,
                        TransbankStatementModel.value_1,
                        TransbankStatementModel.value_2,
                        TransbankStatementModel.value_3,        
                        TransbankStatementModel.value_4,
                        BranchOfficeModel.branch_office.label("branch_office")
                    )
                    .outerjoin(BranchOfficeModel, BranchOfficeModel.id == TransbankStatementModel.branch_office_id)
                    .order_by(TransbankStatementModel.id)
                )

                total_items = data_query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return "Invalid page number"

                data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return "No data found"

                serialized_data = [{
                        "id": transbank_statement.id,
                        "branch_office_id": transbank_statement.branch_office_id,
                        "original_date": transbank_statement.original_date,
                        "code": transbank_statement.code,
                        "branch_office_name": transbank_statement.branch_office_name,
                        "sale_type": transbank_statement.sale_type,
                        "payment_type": transbank_statement.payment_type,
                        "card_number": transbank_statement.card_number,
                        "sale_description": transbank_statement.sale_description,
                        "amount": transbank_statement.amount,
                        "branch_office": transbank_statement.branch_office,
                    } for transbank_statement in data]

                total_available_receipts = self.db.query(TransbankStatementModel).count()

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data,
                    "total_available_receipts": total_available_receipts
                }
            else:
                data_query = self.db.query(TransbankStatementModel.id, 
                                           TransbankStatementModel.branch_office_id, 
                                           TransbankStatementModel.original_date,
                                           TransbankStatementModel.code,
                                           TransbankStatementModel.branch_office_name,
                                           TransbankStatementModel.sale_type,
                                           TransbankStatementModel.payment_type,
                                           TransbankStatementModel.card_number,
                                           TransbankStatementModel.sale_description,
                                           TransbankStatementModel.amount,
                                           TransbankStatementModel.value_1,
                                           TransbankStatementModel.value_2,
                                           TransbankStatementModel.value_3,
                                           TransbankStatementModel.value_4
                                        ). \
                        order_by(TransbankStatementModel.id).all()

                serialized_data = [{
                        "id": transbank_statement.id,
                        "branch_office_id": transbank_statement.branch_office_id,
                        "original_date": transbank_statement.original_date,
                        "code": transbank_statement.code,
                        "branch_office_name": transbank_statement.branch_office_name,
                        "sale_type": transbank_statement.sale_type,
                        "payment_type": transbank_statement.payment_type,
                        "card_number": transbank_statement.card_number,
                        "sale_description": transbank_statement.sale_description,
                        "amount": transbank_statement.amount,
                    } for transbank_statement in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def read_store_bank_statement(self, file_url, period):
        try:
            fixed_period = HelperClass.fix_current_dte_period(period)
            date = fixed_period + "-01"

            self.db.execute(text("TRUNCATE TABLE transbank_statements"))
            self.db.commit()
            response = requests.get(file_url)

            response.raise_for_status()
            content = response.content.decode('latin1')
            lines = content.splitlines()
            start_index = None
            for i, line in enumerate(lines):
                if line.startswith("Fecha Venta"):
                    start_index = i
                    break

            if start_index is None:
                raise HTTPException(status_code=400, detail="El archivo .dat no contiene encabezado de datos.")

            data_lines = "\n".join(lines[start_index:])
            df = pd.read_csv(StringIO(data_lines), delimiter=";", dtype=str)
            df = df.fillna("")
            
            for index, row in df.iterrows():
                branch_office_transbank_statement = self.db.query(BranchOfficesTransbankStatementsModel). \
                        filter(BranchOfficesTransbankStatementsModel.transbank_code == row.get("Fecha Venta", "")). \
                        first()
                
                check_branch_office_transbank_statement = self.db.query(BranchOfficesTransbankStatementsModel). \
                        filter(BranchOfficesTransbankStatementsModel.transbank_code == row.get("Fecha Venta", "")). \
                        count()

                if check_branch_office_transbank_statement > 0:
                    fecha_str = index
                    fecha_dt = datetime.strptime(fecha_str, "%d/%m/%Y %H:%M")
                    fecha_formateada = fecha_dt.strftime("%Y-%m-%d")
                    transbank_statement = TransbankStatementModel()
                    transbank_statement.branch_office_id = branch_office_transbank_statement.branch_office_id if branch_office_transbank_statement else None
                    transbank_statement.original_date = fecha_formateada
                    transbank_statement.code = row.get("Fecha Venta", "")
                    transbank_statement.branch_office_name = row.get("Local", "")
                    transbank_statement.sale_type = row.get("Identificación Local", "")
                    transbank_statement.payment_type = row.get("Tipo Movimiento", "")
                    transbank_statement.card_number = row.get("Tipo Tarjeta", "")
                    transbank_statement.sale_description = row.get("Identificador", "")
                    transbank_statement.amount = int(row.get("Tipo Cuota", "0").replace(".", ""))
                    transbank_statement.value_1 = row.get("Monto Afecto", "")
                    transbank_statement.value_2 = row.get("Monto Exento", "")
                    transbank_statement.value_3 = row.get("Código Autorización", "")
                    transbank_statement.value_4 = row.get("N° Cuotas", "")
                    transbank_statement.added_date = datetime
                    self.db.add(transbank_statement)
                    self.db.commit()

            transbank_total = self.db.query(TransbankTotalModel).all()

            for item in transbank_total:
                cashier = self.db.query(CashierModel). \
                        filter(CashierModel.branch_office_id == item.branch_office_id). \
                        filter(CashierModel.transbank_status_id == 1). \
                        first()
                
                check_cashier = self.db.query(CashierModel). \
                        filter(CashierModel.branch_office_id == item.branch_office_id). \
                        filter(CashierModel.transbank_status_id == 1). \
                        count()
                
                card_net_amount = round(item.total/1.19)

                if check_cashier > 0:
                    check_collection = self.db.query(CollectionModel). \
                        filter(CollectionModel.branch_office_id == item.branch_office_id). \
                        filter(CollectionModel.cashier_id == cashier.id). \
                        filter(CollectionModel.added_date == date). \
                        count()
                    
                    if check_collection > 0:
                        collection = self.db.query(CollectionModel). \
                            filter(CollectionModel.branch_office_id == item.branch_office_id). \
                            filter(CollectionModel.cashier_id == cashier.id). \
                            filter(CollectionModel.added_date == date). \
                            first()

                        collection.card_gross_amount += item.total
                        collection.card_net_amount += card_net_amount
                        collection.total_tickets += item.total_tickets
                        collection.updated_date = item.added_date

                        self.db.commit()
                    else:
                        collection = CollectionModel(
                            branch_office_id=item.branch_office_id,
                            cashier_id=cashier.id,
                            cash_gross_amount=0,
                            cash_net_amount=0,
                            card_gross_amount=item.total,
                            card_net_amount=card_net_amount,
                            total_tickets=item.total_tickets,
                            added_date=date,
                            updated_date= item.original_date,
                        )

                        self.db.add(collection)
                        self.db.commit()

            return 1

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al leer el Transbank: {str(e)}")
