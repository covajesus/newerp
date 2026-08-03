from datetime import datetime
from sqlalchemy.orm import Session
from app.backend.db.models import TransbankStatementModel, BranchOfficesTransbankStatementsModel, BranchOfficeModel, TransbankTotalModel, CollectionModel, CashierModel
from app.backend.classes.helper_class import HelperClass
from app.backend.classes.file_class import FileClass
from fastapi import HTTPException
from sqlalchemy import text
import requests
from io import StringIO
import pandas as pd
import re

class TransbankStatementClass:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _decode_transbank_bytes(raw: bytes) -> str:
        """Decodifica .dat Transbank (UTF-8 con BOM o latin1)."""
        if not raw:
            return ""
        for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
            try:
                return raw.decode(encoding)
            except UnicodeDecodeError:
                continue
        return raw.decode("latin1", errors="replace")

    @staticmethod
    def _normalize_header_line(line: str) -> str:
        return (line or "").replace("\ufeff", "").strip().strip('"').strip("'")

    @staticmethod
    def _normalize_column_name(name: str) -> str:
        text = str(name or "").replace("\ufeff", "").strip().strip('"').strip("'")
        text = re.sub(r"\s+", " ", text)
        return text.lower()

    # Alias por campo lógico → variantes legacy y formato nuevo Transbank.
    _COLUMN_ALIASES = {
        "fecha": (
            "Fecha Venta",
            "Fecha de movimiento",
            "Fecha de abono",
            "Fecha de venta",
        ),
        "local_id": (
            "Local",
            "Codigo de comercio",
            "Código de comercio",
        ),
        "local_name": (
            "Identificación Local",
            "Identificacion Local",
            "Nombre local",
        ),
        "sale_type": (
            "Tipo Movimiento",
            "Tipo de movimiento",
        ),
        "payment_type": (
            "Tipo Tarjeta",
            "Tipo de tarjeta",
            "Medio de pago",
        ),
        "card_number": (
            "Identificador",
            "Numero de tarjeta",
            "Número de tarjeta",
        ),
        "sale_description": (
            "Tipo Cuota",
            "Estado de movimiento",
            "Medio de pago",
        ),
        "monto_afecto": (
            "Monto Afecto",
            "Monto afecto",
            "Monto original de la venta",
        ),
        "monto_exento": (
            "Monto Exento",
            "Monto exento",
        ),
        "auth_code": (
            "Código Autorización",
            "Codigo Autorizacion",
            "Codigo de autorizacion",
            "Código de autorización",
        ),
        "cuotas": (
            "N° Cuotas",
            "N Cuotas",
            "Numero de cuotas",
            "Número de cuotas",
        ),
    }

    @classmethod
    def _build_column_map(cls, columns) -> dict:
        """Mapa campo lógico → nombre real de columna en el DataFrame."""
        by_norm = {cls._normalize_column_name(col): col for col in columns}
        resolved = {}
        for field, aliases in cls._COLUMN_ALIASES.items():
            for alias in aliases:
                key = cls._normalize_column_name(alias)
                if key in by_norm:
                    resolved[field] = by_norm[key]
                    break
        return resolved

    @classmethod
    def _row_get(cls, row, colmap: dict, field: str, default: str = "") -> str:
        col = colmap.get(field)
        if not col:
            return default
        value = row.get(col, default)
        if value is None:
            return default
        return str(value).strip()

    @staticmethod
    def _parse_amount(raw: str) -> int:
        """
        Convierte montos Transbank a entero CLP.
        Formato nuevo: '150,00' / '2.350,00' (miles con punto, decimales con coma).
        Legacy: '12345' o '12.345' (punto como miles, sin decimales).
        """
        text = (raw or "").strip()
        if text in ("", "-", "None"):
            return 0
        negative = text.startswith("-")
        text = text.lstrip("-").strip().replace(" ", "")
        if not text:
            return 0
        try:
            if "," in text:
                # Chileno: quitar puntos de miles; coma = decimal (p.ej. 2.350,00 → 2350)
                int_part, _, dec_part = text.partition(",")
                int_part = int_part.replace(".", "")
                value = float(f"{int_part}.{dec_part}") if dec_part else float(int_part)
            elif "." in text:
                parts = text.split(".")
                # Un solo punto y 1–2 decimales → decimal estilo US (89500.00)
                if len(parts) == 2 and 1 <= len(parts[1]) <= 2 and parts[0].isdigit() and parts[1].isdigit():
                    value = float(text)
                else:
                    # Puntos como separador de miles (12.345 o 1.234.567)
                    value = float(text.replace(".", ""))
            else:
                value = float(text)
            amount = int(round(value))
            return -amount if negative else amount
        except (TypeError, ValueError):
            return 0

    @classmethod
    def _parse_transbank_date(cls, raw_date: str):
        text = (raw_date or "").strip().lstrip("*")
        if not text:
            return None
        for fmt in (
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%d-%m-%Y %H:%M",
            "%d-%m-%Y",
        ):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None

    @classmethod
    def _is_transbank_header_line(cls, line: str) -> bool:
        """
        True si la fila parece el encabezado de detalle Transbank.
        Soporta formato legacy ('Fecha Venta;Local;...') y nuevo
        ('Tipo de movimiento;...;Fecha de movimiento;...;Codigo de comercio;...').
        """
        normalized = cls._normalize_header_line(line)
        if not normalized or ";" not in normalized:
            return False
        lower = normalized.lower()
        legacy = ("fecha venta" in lower) and ("local" in lower)
        modern = (
            ("fecha de movimiento" in lower or "fecha de abono" in lower)
            and ("codigo de comercio" in lower or "código de comercio" in lower)
        )
        return legacy or modern

    @classmethod
    def _find_transbank_header_index(cls, lines) -> int | None:
        for i, line in enumerate(lines):
            if cls._is_transbank_header_line(line):
                return i
        for i, line in enumerate(lines):
            lower = cls._normalize_header_line(line).lower()
            if (
                "fecha venta" in lower
                or "fecha de movimiento" in lower
                or "codigo de comercio" in lower
                or "código de comercio" in lower
            ) and ";" in lower:
                return i
        return None

    @staticmethod
    def _transbank_file_preview(lines, max_lines: int = 8) -> str:
        preview_lines = []
        for line in lines:
            text = (line or "").replace("\ufeff", "").strip()
            if not text:
                continue
            preview_lines.append(text[:160])
            if len(preview_lines) >= max_lines:
                break
        if not preview_lines:
            return "(archivo vacío)"
        return " | ".join(preview_lines)

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
                total_pages = (total_items + items_per_page - 1) // items_per_page if total_items else 0

                # Tabla vacía: devolver listado vacío (no "Invalid page number").
                if total_items == 0:
                    return {
                        "total_items": 0,
                        "total_pages": 0,
                        "current_page": page if page >= 1 else 1,
                        "items_per_page": items_per_page,
                        "data": [],
                        "total_available_receipts": 0,
                    }

                if page < 1 or page > total_pages:
                    return "Invalid page number"

                data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

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

    def read_store_bank_statement(self, file_url, period, progress_callback=None):
        try:
            if progress_callback:
                progress_callback(5, "Preparando procesamiento...")
                
            fixed_period = HelperClass.fix_current_dte_period(period)
            date = fixed_period + "-01"

            if progress_callback:
                progress_callback(10, "Limpiando tabla anterior...")

            # DELETE completo de la tabla antes de cargar el Transbank
            # Usar DELETE en lugar de TRUNCATE para respetar las claves foráneas
            self.db.execute(text("DELETE FROM transbank_statements"))
            self.db.commit()

            if progress_callback:
                progress_callback(15, "Leyendo archivo...")

            # Verificar si la URL es del servidor local y leer directamente del filesystem
            base_url = "https://intrajisbackend.com/files"
            local_urls = [
                "https://intrajisbackend.com/files",
                "http://127.0.0.1:8000/files",
                "http://localhost:8000/files",
                "http://127.0.0.1:8085/files",
                "http://localhost:8085/files",
            ]
            
            # Si es una URL local, leer directamente del filesystem
            is_local_url = any(file_url.startswith(url) for url in local_urls)
            
            if is_local_url:
                # Extraer el remote_path de la URL
                # Formato esperado: https://intrajisbackend.com/files/transbank_statements_xxx.dat
                for url_prefix in local_urls:
                    if file_url.startswith(url_prefix):
                        remote_path = file_url[len(url_prefix):].lstrip('/')
                        break
                
                # Leer el archivo directamente del filesystem usando FileClass
                file_class = FileClass(self.db)
                file_content = file_class.download(remote_path)
                content = self._decode_transbank_bytes(file_content)
            else:
                # Si es una URL externa, usar requests
                response = requests.get(file_url)
                response.raise_for_status()
                content = self._decode_transbank_bytes(response.content)
            
            lines = content.splitlines()
            
            if progress_callback:
                progress_callback(25, "Analizando estructura del archivo...")
                
            start_index = self._find_transbank_header_index(lines)

            if start_index is None:
                preview = self._transbank_file_preview(lines)
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "El archivo .dat no contiene encabezado de datos. "
                        "Se espera formato Transbank con 'Fecha Venta' (legacy) "
                        "o 'Fecha de movimiento' + 'Codigo de comercio' (nuevo). "
                        f"Vista previa: {preview}"
                    ),
                )

            data_lines = "\n".join(lines[start_index:])
            df = pd.read_csv(
                StringIO(data_lines),
                delimiter=";",
                dtype=str,
                index_col=False,
                quotechar='"',
            )
            df = df.fillna("")
            # Normalizar nombres de columnas (BOM, espacios, comillas).
            df.columns = [
                str(col).replace("\ufeff", "").strip().strip('"').strip("'")
                for col in df.columns
            ]

            colmap = self._build_column_map(df.columns)
            if "fecha" not in colmap or "local_id" not in colmap:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Encabezado Transbank incompleto: faltan fecha y/o código de local. "
                        f"Columnas leídas: {list(df.columns)[:15]} | "
                        f"Mapeadas: {colmap}"
                    ),
                )
            
            total_rows = len(df)
            if progress_callback:
                progress_callback(35, f"📊 Iniciando procesamiento de {total_rows} transacciones...")
            
            processed_transactions = set()  # Para evitar duplicados en el mismo archivo
            batch_size = 50  # Lotes más pequeños para commits más frecuentes
            batch_count = 0
            
            # Crear cache de branch offices para evitar consultas repetidas
            branch_office_cache = {}
            
            for index, row in df.iterrows():
                # Calcular progreso más granular (35% a 85% para el procesamiento de filas)
                progress_percent = 35 + ((index / total_rows) * 50)  # Usar float para más precisión
                progress_percent = round(progress_percent, 1)  # Redondear a 1 decimal
                
                # Actualizar progreso mucho más frecuentemente - cada 5 registros o cada 0.5% de progreso
                update_frequency = max(5, total_rows // 200)  # Cada 0.5% o mínimo cada 5 registros
                
                if progress_callback and (index % update_frequency == 0 or index == total_rows - 1):
                    progress_callback(progress_percent, f"⚡ Procesando transacción {index + 1} de {total_rows} ({progress_percent}%)")
                
                local_id = self._row_get(row, colmap, "local_id")
                if not local_id:
                    continue
                
                # Usar cache para branch offices
                if local_id not in branch_office_cache:
                    branch_office_transbank_statement = self.db.query(BranchOfficesTransbankStatementsModel). \
                            filter(BranchOfficesTransbankStatementsModel.transbank_code == local_id). \
                            first()
                    branch_office_cache[local_id] = branch_office_transbank_statement
                else:
                    branch_office_transbank_statement = branch_office_cache[local_id]

                if branch_office_transbank_statement:
                    raw_date = self._row_get(row, colmap, "fecha")
                    parsed_date = self._parse_transbank_date(raw_date)

                    if not parsed_date:
                        raise ValueError(f"Invalid date format: '{raw_date}'")

                    formatted_date = parsed_date.strftime("%Y-%m-%d")
                    
                    monto_afecto_raw = self._row_get(row, colmap, "monto_afecto", "0")
                    amount = self._parse_amount(monto_afecto_raw)
                    card_number = self._row_get(row, colmap, "card_number")
                    auth_code = self._row_get(row, colmap, "auth_code")
                    
                    transaction_key = (
                        local_id,
                        formatted_date,
                        card_number,
                        auth_code,
                        amount,
                    )
                    
                    # Evitar duplicados en el mismo archivo
                    if transaction_key in processed_transactions:
                        continue
                    
                    processed_transactions.add(transaction_key)
                    
                    # Verificar si ya existe en la base de datos
                    existing_transaction = self.db.query(TransbankStatementModel).filter(
                        TransbankStatementModel.code == local_id,
                        TransbankStatementModel.original_date == formatted_date,
                        TransbankStatementModel.card_number == card_number,
                        TransbankStatementModel.value_3 == auth_code,
                        TransbankStatementModel.amount == amount,
                    ).first()
                    
                    if existing_transaction:
                        continue  # Skip si ya existe
                    
                    transbank_statement = TransbankStatementModel()
                    transbank_statement.branch_office_id = branch_office_transbank_statement.branch_office_id if branch_office_transbank_statement else None
                    transbank_statement.original_date = formatted_date
                    transbank_statement.code = local_id
                    transbank_statement.branch_office_name = self._row_get(row, colmap, "local_name")
                    transbank_statement.sale_type = self._row_get(row, colmap, "sale_type")
                    transbank_statement.payment_type = self._row_get(row, colmap, "payment_type")
                    transbank_statement.card_number = card_number
                    transbank_statement.sale_description = self._row_get(row, colmap, "sale_description")
                    transbank_statement.amount = amount
                    transbank_statement.value_1 = monto_afecto_raw
                    transbank_statement.value_2 = self._row_get(row, colmap, "monto_exento")
                    transbank_statement.value_3 = auth_code
                    transbank_statement.value_4 = self._row_get(row, colmap, "cuotas")
                    transbank_statement.added_date = formatted_date
                    self.db.add(transbank_statement)
                    
                    batch_count += 1
                    
                    # Commit en lotes para mejorar performance
                    if batch_count >= batch_size:
                        if progress_callback:
                            progress_callback(progress_percent, f"💾 Guardando lote de {batch_count} transacciones... ({progress_percent}%)")
                        self.db.commit()
                        batch_count = 0

            # Commit final para cualquier transacción restante
            if batch_count > 0:
                if progress_callback:
                    progress_callback(82, f"💾 Guardando lote final de {batch_count} transacciones...")
                self.db.commit()

            if progress_callback:
                progress_callback(85, "Procesando totales y colecciones...")

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

            if progress_callback:
                progress_callback(100, "Procesamiento completado exitosamente")
            
            if progress_callback:
                progress_callback(100, "Procesamiento completado exitosamente")

            return 1

        except Exception as e:
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error al leer el Transbank: {str(e)}")

