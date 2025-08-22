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
                    .order_by(TransbankStatementModel.id.desc())
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

            # TRUNCATE completo de la tabla antes de cargar el Transbank
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
            df = pd.read_csv(StringIO(data_lines), delimiter=";", dtype=str, index_col=False)
            df = df.fillna("")
            
            processed_transactions = set()  # Para evitar duplicados en el mismo archivo
            
            for index, row in df.iterrows():
                # Ahora las columnas están correctamente mapeadas
                local_id = row.get("Local", "")  # ID del local
                
                branch_office_transbank_statement = self.db.query(BranchOfficesTransbankStatementsModel). \
                        filter(BranchOfficesTransbankStatementsModel.transbank_code == local_id). \
                        first()
                
                check_branch_office_transbank_statement = self.db.query(BranchOfficesTransbankStatementsModel). \
                        filter(BranchOfficesTransbankStatementsModel.transbank_code == local_id). \
                        count()

                if check_branch_office_transbank_statement > 0:
                    # La fecha está en la columna "Fecha Venta"
                    raw_date = row.get("Fecha Venta", "").strip().lstrip("*")

                    # Try parsing the date with possible formats
                    parsed_date = None
                    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
                        try:
                            parsed_date = datetime.strptime(raw_date, fmt)
                            break
                        except ValueError:
                            continue

                    if not parsed_date:
                        raise ValueError(f"Invalid date format: '{raw_date}'")

                    formatted_date = parsed_date.strftime("%Y-%m-%d")
                    
                    # Crear una clave única para evitar duplicados
                    monto_afecto = row.get("Monto Afecto", "0")
                    if monto_afecto == "" or monto_afecto == "-":
                        monto_afecto = "0"
                    
                    transaction_key = (
                        local_id,
                        formatted_date,
                        row.get("Identificador", ""),
                        row.get("Código Autorización", ""),
                        monto_afecto
                    )
                    
                    # Evitar duplicados en el mismo archivo
                    if transaction_key in processed_transactions:
                        continue
                    
                    processed_transactions.add(transaction_key)
                    
                    # Verificar si ya existe en la base de datos
                    existing_transaction = self.db.query(TransbankStatementModel).filter(
                        TransbankStatementModel.code == local_id,
                        TransbankStatementModel.original_date == formatted_date,
                        TransbankStatementModel.card_number == row.get("Identificador", ""),
                        TransbankStatementModel.value_3 == row.get("Código Autorización", ""),
                        TransbankStatementModel.amount == int(monto_afecto.replace(".", "").replace(",", ""))
                    ).first()
                    
                    if existing_transaction:
                        continue  # Skip si ya existe
                    
                    transbank_statement = TransbankStatementModel()
                    transbank_statement.branch_office_id = branch_office_transbank_statement.branch_office_id if branch_office_transbank_statement else None
                    transbank_statement.original_date = formatted_date
                    transbank_statement.code = local_id  # ID del local
                    transbank_statement.branch_office_name = row.get("Identificación Local", "")  # Nombre del local
                    transbank_statement.sale_type = row.get("Tipo Movimiento", "")
                    transbank_statement.payment_type = row.get("Tipo Tarjeta", "")
                    transbank_statement.card_number = row.get("Identificador", "")
                    transbank_statement.sale_description = row.get("Tipo Cuota", "")
                    transbank_statement.amount = int(monto_afecto.replace(".", "").replace(",", ""))
                    transbank_statement.value_1 = row.get("Monto Afecto", "")
                    transbank_statement.value_2 = row.get("Monto Exento", "")
                    transbank_statement.value_3 = row.get("Código Autorización", "")
                    transbank_statement.value_4 = row.get("N° Cuotas", "")
                    transbank_statement.added_date = formatted_date
                    self.db.add(transbank_statement)
                    self.db.commit()

            # Procesar totales y colecciones con mejor control de duplicados
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
                    # Eliminar colecciones existentes del período específico para evitar duplicados
                    existing_collections = self.db.query(CollectionModel). \
                        filter(CollectionModel.branch_office_id == item.branch_office_id). \
                        filter(CollectionModel.cashier_id == cashier.id). \
                        filter(CollectionModel.added_date == item.added_date). \
                        all()

                    for existing_collection in existing_collections:
                        self.db.delete(existing_collection)
                    
                    self.db.commit()

                    # Crear nueva colección
                    collection = CollectionModel(
                            branch_office_id=item.branch_office_id,
                            cashier_id=cashier.id,
                            cash_gross_amount=0,
                            cash_net_amount=0,
                            card_gross_amount=item.total,
                            card_net_amount=card_net_amount,
                            total_tickets=item.total_tickets,
                            added_date=item.added_date,
                            updated_date=item.added_date,
                        )

                    self.db.add(collection)
                    self.db.commit()

            return 1

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al leer el Transbank: {str(e)}")

    def read_store_bank_statement_with_progress(self, file_url, period, progress_callback=None):
        """Versión con callback de progreso para barra de progreso en tiempo real"""
        try:
            if progress_callback:
                progress_callback(5, "Preparando procesamiento...")
                
            fixed_period = HelperClass.fix_current_dte_period(period)
            date = fixed_period + "-01"

            # TRUNCATE completo de la tabla antes de cargar el Transbank
            self.db.execute(text("TRUNCATE TABLE transbank_statements"))
            self.db.commit()
            
            if progress_callback:
                progress_callback(15, "Descargando archivo...")

            response = requests.get(file_url)
            response.raise_for_status()
            content = response.content.decode('latin1')
            lines = content.splitlines()
            
            if progress_callback:
                progress_callback(25, "Analizando estructura del archivo...")
                
            start_index = None
            for i, line in enumerate(lines):
                if line.startswith("Fecha Venta"):
                    start_index = i
                    break

            if start_index is None:
                raise HTTPException(status_code=400, detail="El archivo .dat no contiene encabezado de datos.")

            data_lines = "\n".join(lines[start_index:])
            df = pd.read_csv(StringIO(data_lines), delimiter=";", dtype=str, index_col=False)
            df = df.fillna("")
            
            total_rows = len(df)
            if progress_callback:
                progress_callback(35, f"Procesando {total_rows} transacciones...")
            
            processed_transactions = set()
            batch_size = 100  # Procesar en lotes de 100 transacciones
            batch_count = 0
            
            for index, row in df.iterrows():
                # Calcular progreso (35% a 85% para el procesamiento de filas)
                progress_percent = 35 + int((index / total_rows) * 50)
                
                # Actualizar progreso más frecuentemente basado en el tamaño del archivo
                update_frequency = max(1, min(50, total_rows // 20))  # Entre 1 y 50, dependiendo del tamaño
                
                if progress_callback and (index % update_frequency == 0 or index == total_rows - 1):
                    progress_callback(progress_percent, f"Procesando transacción {index + 1} de {total_rows} ({progress_percent}%)")
                
                # Resto del código igual al método original
                local_id = row.get("Local", "")
                
                branch_office_transbank_statement = self.db.query(BranchOfficesTransbankStatementsModel). \
                        filter(BranchOfficesTransbankStatementsModel.transbank_code == local_id). \
                        first()
                
                check_branch_office_transbank_statement = self.db.query(BranchOfficesTransbankStatementsModel). \
                        filter(BranchOfficesTransbankStatementsModel.transbank_code == local_id). \
                        count()

                if check_branch_office_transbank_statement > 0:
                    raw_date = row.get("Fecha Venta", "").strip().lstrip("*")

                    parsed_date = None
                    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
                        try:
                            parsed_date = datetime.strptime(raw_date, fmt)
                            break
                        except ValueError:
                            continue

                    if not parsed_date:
                        raise ValueError(f"Invalid date format: '{raw_date}'")

                    formatted_date = parsed_date.strftime("%Y-%m-%d")
                    
                    monto_afecto = row.get("Monto Afecto", "0")
                    if monto_afecto == "" or monto_afecto == "-":
                        monto_afecto = "0"
                    
                    transaction_key = (
                        local_id,
                        formatted_date,
                        row.get("Identificador", ""),
                        row.get("Código Autorización", ""),
                        monto_afecto
                    )
                    
                    if transaction_key in processed_transactions:
                        continue
                    
                    processed_transactions.add(transaction_key)
                    
                    existing_transaction = self.db.query(TransbankStatementModel).filter(
                        TransbankStatementModel.code == local_id,
                        TransbankStatementModel.original_date == formatted_date,
                        TransbankStatementModel.card_number == row.get("Identificador", ""),
                        TransbankStatementModel.value_3 == row.get("Código Autorización", ""),
                        TransbankStatementModel.amount == int(monto_afecto.replace(".", "").replace(",", ""))
                    ).first()
                    
                    if existing_transaction:
                        continue
                    
                    transbank_statement = TransbankStatementModel()
                    transbank_statement.branch_office_id = branch_office_transbank_statement.branch_office_id if branch_office_transbank_statement else None
                    transbank_statement.original_date = formatted_date
                    transbank_statement.code = local_id
                    transbank_statement.branch_office_name = row.get("Identificación Local", "")
                    transbank_statement.sale_type = row.get("Tipo Movimiento", "")
                    transbank_statement.payment_type = row.get("Tipo Tarjeta", "")
                    transbank_statement.card_number = row.get("Identificador", "")
                    transbank_statement.sale_description = row.get("Tipo Cuota", "")
                    transbank_statement.amount = int(monto_afecto.replace(".", "").replace(",", ""))
                    transbank_statement.value_1 = row.get("Monto Afecto", "")
                    transbank_statement.value_2 = row.get("Monto Exento", "")
                    transbank_statement.value_3 = row.get("Código Autorización", "")
                    transbank_statement.value_4 = row.get("N° Cuotas", "")
                    transbank_statement.added_date = formatted_date
                    self.db.add(transbank_statement)
                    
                    batch_count += 1
                    
                    # Commit en lotes para mejorar performance
                    if batch_count >= batch_size or index == total_rows - 1:
                        if progress_callback:
                            progress_callback(progress_percent, f"Guardando lote de {batch_count} transacciones...")
                        self.db.commit()
                        batch_count = 0

            if progress_callback:
                progress_callback(85, "Procesando totales y colecciones...")

            # Procesar totales y colecciones (código igual al método original)
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
                    existing_collections = self.db.query(CollectionModel). \
                        filter(CollectionModel.branch_office_id == item.branch_office_id). \
                        filter(CollectionModel.cashier_id == cashier.id). \
                        filter(CollectionModel.added_date == item.added_date). \
                        all()

                    for existing_collection in existing_collections:
                        self.db.delete(existing_collection)
                    
                    self.db.commit()

                    collection = CollectionModel(
                            branch_office_id=item.branch_office_id,
                            cashier_id=cashier.id,
                            cash_gross_amount=0,
                            cash_net_amount=0,
                            card_gross_amount=item.total,
                            card_net_amount=card_net_amount,
                            total_tickets=item.total_tickets,
                            added_date=item.added_date,
                            updated_date=item.added_date,
                        )

                    self.db.add(collection)
                    self.db.commit()

            if progress_callback:
                progress_callback(95, "Finalizando procesamiento...")

            return 1

        except Exception as e:
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error al leer el Transbank: {str(e)}")
