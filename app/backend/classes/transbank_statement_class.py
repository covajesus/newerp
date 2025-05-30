from datetime import datetime
from sqlalchemy.orm import Session
from app.backend.db.models import TransbankStatementModel, BranchOfficesTransbankStatementsModel, ComparationPendingDtesBankStatementModel, DteModel, ComparationPendingDepositsBankStatementModel, DepositModel
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

    def get_comparation_pending_deposits_bank_statements(self, page=1, items_per_page=99999999):
        try:
            if page != 0:
                data_query = self.db.query(ComparationPendingDepositsBankStatementModel.id, 
                                           ComparationPendingDepositsBankStatementModel.branch_office_id, 
                                           ComparationPendingDepositsBankStatementModel.payment_type_id, 
                                           ComparationPendingDepositsBankStatementModel.collection_id, 
                                           ComparationPendingDepositsBankStatementModel.branch_office, 
                                           ComparationPendingDepositsBankStatementModel.status_id, 
                                           ComparationPendingDepositsBankStatementModel.payment_number, 
                                           ComparationPendingDepositsBankStatementModel.collection_amount, 
                                           ComparationPendingDepositsBankStatementModel.collection_date, 
                                           ComparationPendingDepositsBankStatementModel.deposited_amount, 
                                           ComparationPendingDepositsBankStatementModel.bank_statement_type_id,
                                           ComparationPendingDepositsBankStatementModel.bank_statement_amount, 
                                           ComparationPendingDepositsBankStatementModel.bank_statement_rut, 
                                           ComparationPendingDepositsBankStatementModel.deposit_number). \
                        order_by(ComparationPendingDepositsBankStatementModel.id)

                total_items = data_query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return "Invalid page number"

                data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return "No data found"

                serialized_data = [{
                        "id": bank_statement.id,
                        "branch_office_id": bank_statement.branch_office_id,
                        "payment_type_id": bank_statement.payment_type_id,
                        "collection_id": bank_statement.collection_id,
                        "branch_office": bank_statement.branch_office,
                        "status_id": bank_statement.status_id,
                        "payment_number": bank_statement.payment_number,
                        "collection_amount": bank_statement.collection_amount,
                        "collection_date": bank_statement.collection_date,
                        "deposited_amount": bank_statement.deposited_amount,
                        "bank_statement_type_id": bank_statement.bank_statement_type_id,
                        "bank_statement_amount": bank_statement.bank_statement_amount,
                        "bank_statement_rut": bank_statement.bank_statement_rut,
                        "deposit_number": bank_statement.deposit_number
                    } for bank_statement in data]

                total_available_receipts = self.db.query(ComparationPendingDepositsBankStatementModel).filter(ComparationPendingDepositsBankStatementModel.bank_statement_type_id == 1).count()

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data,
                    "total_available_receipts": total_available_receipts
                }
            else:
                data_query = self.db.query(
                                            ComparationPendingDepositsBankStatementModel.id, 
                                           ComparationPendingDepositsBankStatementModel.branch_office_id, 
                                           ComparationPendingDepositsBankStatementModel.payment_type_id, 
                                           ComparationPendingDepositsBankStatementModel.collection_id, 
                                           ComparationPendingDepositsBankStatementModel.branch_office, 
                                           ComparationPendingDepositsBankStatementModel.status_id, 
                                           ComparationPendingDepositsBankStatementModel.payment_number, 
                                           ComparationPendingDepositsBankStatementModel.collection_amount, 
                                           ComparationPendingDepositsBankStatementModel.collection_date, 
                                           ComparationPendingDepositsBankStatementModel.deposited_amount, 
                                           ComparationPendingDepositsBankStatementModel.bank_statement_type_id,
                                           ComparationPendingDepositsBankStatementModel.bank_statement_amount, 
                                           ComparationPendingDepositsBankStatementModel.bank_statement_rut, 
                                           ComparationPendingDepositsBankStatementModel.deposit_number
                                        ). \
                        order_by(ComparationPendingDepositsBankStatementModel.id).all()

                serialized_data = [{
                        "id": bank_statement.id,
                        "branch_office_id": bank_statement.branch_office_id,
                        "payment_type_id": bank_statement.payment_type_id,
                        "collection_id": bank_statement.collection_id,
                        "branch_office": bank_statement.branch_office,
                        "status_id": bank_statement.status_id,
                        "payment_number": bank_statement.payment_number,
                        "collection_amount": bank_statement.collection_amount,
                        "collection_date": bank_statement.collection_date,
                        "deposited_amount": bank_statement.deposited_amount,
                        "bank_statement_type_id": bank_statement.bank_statement_type_id,
                        "bank_statement_amount": bank_statement.bank_statement_amount,
                        "bank_statement_rut": bank_statement.bank_statement_rut,
                        "deposit_number": bank_statement.deposit_number
                    } for bank_statement in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get_comparation_pending_dtes_bank_statements(self, page=1, items_per_page=99999999):
        try:
            if page != 0:
                data_query = self.db.query(ComparationPendingDtesBankStatementModel.id, ComparationPendingDtesBankStatementModel.rut, ComparationPendingDtesBankStatementModel.customer, ComparationPendingDtesBankStatementModel.folio, ComparationPendingDtesBankStatementModel.branch_office, ComparationPendingDtesBankStatementModel.amount, ComparationPendingDtesBankStatementModel.bank_statement_period, ComparationPendingDtesBankStatementModel.bank_statement_amount, ComparationPendingDtesBankStatementModel.bank_statement_rut, ComparationPendingDtesBankStatementModel.deposit_number). \
                        order_by(ComparationPendingDtesBankStatementModel.id)

                total_items = data_query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return "Invalid page number"

                data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return "No data found"

                serialized_data = [{
                        "id": bank_statement.id,
                        "rut": bank_statement.rut,
                        "customer": bank_statement.customer,
                        "folio": bank_statement.folio,
                        "branch_office": bank_statement.branch_office,
                        "amount": bank_statement.amount,
                        "bank_statement_period": bank_statement.bank_statement_period,
                        "bank_statement_amount": bank_statement.bank_statement_amount,
                        "bank_statement_rut": bank_statement.bank_statement_rut,
                        "deposit_number": bank_statement.deposit_number,
                    } for bank_statement in data]

                total_available_receipts = self.db.query(ComparationPendingDtesBankStatementModel).filter(ComparationPendingDtesBankStatementModel.bank_statement_type_id == 1).count()

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data,
                    "total_available_receipts": total_available_receipts
                }
            else:
                data_query = self.db.query(ComparationPendingDtesBankStatementModel.id, ComparationPendingDtesBankStatementModel.rut, ComparationPendingDtesBankStatementModel.customer, ComparationPendingDtesBankStatementModel.folio, ComparationPendingDtesBankStatementModel.branch_office, ComparationPendingDtesBankStatementModel.amount, ComparationPendingDtesBankStatementModel.bank_statement_period, ComparationPendingDtesBankStatementModel.bank_statement_amount, ComparationPendingDtesBankStatementModel.bank_statement_rut, ComparationPendingDtesBankStatementModel.deposit_number). \
                        order_by(ComparationPendingDtesBankStatementModel.id).all()

                serialized_data = [{
                        "id": bank_statement.id,
                        "rut": bank_statement.rut,
                        "customer": bank_statement.customer,
                        "folio": bank_statement.folio,
                        "branch_office": bank_statement.branch_office,
                        "amount": bank_statement.amount,
                        "bank_statement_period": bank_statement.bank_statement_period,
                        "bank_statement_amount": bank_statement.bank_statement_amount,
                        "bank_statement_rut": bank_statement.bank_statement_rut,
                        "deposit_number": bank_statement.deposit_number,
                    } for bank_statement in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def read_store_bank_statement(self, file_url, period):
        try:
            self.db.execute(text("TRUNCATE TABLE transbank_statements"))
            self.db.commit()  # Si es necesario hacer un commit
            # Descarga el archivo como texto
            response = requests.get(file_url)

            response.raise_for_status()
            content = response.content.decode('latin1')
            # Encuentra la línea donde comienzan los datos (cabecera de tabla)
            lines = content.splitlines()
            start_index = None
            for i, line in enumerate(lines):
                if line.startswith("Fecha Venta"):
                    start_index = i
                    break

            if start_index is None:
                raise HTTPException(status_code=400, detail="El archivo .dat no contiene encabezado de datos.")

            # Crea un nuevo archivo virtual solo con la tabla
            data_lines = "\n".join(lines[start_index:])
            df = pd.read_csv(StringIO(data_lines), delimiter=";", dtype=str)
            df = df.fillna("")
            
            # Procesamiento de datos como en tu código original
            for index, row in df.iterrows():
                brannch_office_transbank_statement = self.db.query(BranchOfficesTransbankStatementsModel). \
                        filter(BranchOfficesTransbankStatementsModel.transbank_code == row.get("Fecha Venta", "")). \
                        first()

                transbank_statement = TransbankStatementModel()
                transbank_statement.branch_office_id = brannch_office_transbank_statement.branch_office_id if brannch_office_transbank_statement else None
                transbank_statement.added_date = datetime.now()
                transbank_statement.original_date = row.get("Name", "")
                self.db.add(transbank_statement)
                self.db.commit()
                
            
            exit()

            return bank_statement

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al leer el Transbank: {str(e)}")
            
    def customer_accept(self, id):
        dte = self.db.query(DteModel).filter(DteModel.id == id).first()
        dte.status_id = 5

        self.db.add(dte)
        self.db.commit()

    def deposit_accept(self, id):
        dte = self.db.query(DepositModel).filter(DepositModel.id == id).first()
        dte.status_id = 6

        self.db.add(dte)
        self.db.commit()

