from app.backend.db.models import FolioModel, CashierModel, FolioReportModel, FolioQuantityPerCashierModel
from app.backend.classes.setting_class import SettingClass
from app.backend.classes.alert_class import AlertClass
from sqlalchemy import text
import json
import os
import requests
import pytz
import datetime

SIMPLEFACTURA_RUT_EMISOR = "76063822-6"
SIMPLEFACTURA_SUCURSAL = "Casa Matriz"
JISBACKEND_SETTINGS_TOKEN_URL = os.getenv(
    "JISBACKEND_SETTINGS_TOKEN_URL",
    "https://jisbackend.com/api/settings/get_token",
)
SF_FOLIOS_CONSULTAR_TIMEOUT = int(os.getenv("SF_FOLIOS_CONSULTAR_TIMEOUT", "180"))
# Piso de asignación de folios de boleta (39): los CAF anteriores a este número
# fueron consumidos parcialmente por canales que no registran en DB1/DB2, así que
# solo se asigna desde el CAF 32.180.031–32.680.030 (2026-07-21) hacia arriba.
# Piso boleta: solo asignar desde este folio hacia arriba (nunca CAFs viejos).
# Tras agotar 32.180.031–32.680.030 el siguiente CAF válido empieza en 32.680.031+.
FOLIO_ALLOCATION_MIN_39 = int(os.getenv("FOLIO_ALLOCATION_MIN_39", "32680031"))

class FolioClass:
    def __init__(self, db):
        self.db = db

    # Funcion para obtener a todos los folios con paginacion
    def get_all(self, page=0, items_per_page=10):
        try:
            if page != 0:
                data_query = self.db.query(FolioModel.id, FolioModel.folio, FolioModel.billed_status_id, FolioModel.branch_office_id, FolioModel.cashier_id, FolioModel.requested_status_id, FolioModel.used_status_id, FolioModel.added_date). \
                        order_by(FolioModel.folio)

                total_items = data_query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return "Invalid page number"

                data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return "No data found"

                serialized_data = [{
                        "id": folio.id,
                        "folio": folio.folio,
                        "branch_office_id": folio.branch_office_id,
                        "cashier_id": folio.cashier_id,
                        "billed_status_id": folio.billed_status_id,
                        "requested_status_id": folio.requested_status_id,
                        "used_status_id": folio.used_status_id,
                        "added_date": folio.added_date,
                    } for folio in data]

                total_available_receipts = self.db.query(FolioModel).filter(FolioModel.requested_status_id == 0).count()
                print(total_available_receipts)
                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data,
                    "total_available_receipts": total_available_receipts
                }
            else:
                data_query = self.db.query(FolioModel.id, FolioModel.folio, FolioModel.branch_office_id, FolioModel.cashier_id, FolioModel.requested_status_id, FolioModel.used_status_id). \
                        order_by(FolioModel.folio).all()

                serialized_data = [{
                        "id": folio.id,
                        "folio": folio.folio,
                        "branch_office_id": folio.branch_office_id,
                        "cashier_id": folio.cashier_id,
                        "requested_status_id": folio.requested_status_id,
                        "used_status_id": folio.used_status_id,
                    } for folio in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def report(self):
        folio_reports = self.db.query(FolioReportModel).all()

        if not folio_reports:
            return "No hay folios en el informe."
        
        serialized_data = []
        for folio_report in folio_reports:
            folio_report_dict = {
                "id": folio_report.id,
                "cashier": folio_report.cashier,
                "branch_office": folio_report.branch_office,
                "available_folios": folio_report.available_folios,
                "rustdesk": folio_report.rustdesk,
                "anydesk": folio_report.anydesk
            }
            serialized_data.append(folio_report_dict)

        return json.dumps(serialized_data)
    
    def get_quantity_per_cashier(self):
        folio_reports = self.db.query(FolioQuantityPerCashierModel).all()

        if not folio_reports:
            return "No hay folios en el informe."
        
        serialized_data = []
        for folio_report in folio_reports:
            folio_report_dict = {
                "id": folio_report.id,
                "cashier": folio_report.cashier,
                "branch_office": folio_report.branch_office,
                "available_folios": folio_report.available_folios,
                "rustdesk": folio_report.rustdesk,
                "anydesk": folio_report.anydesk
            }
            serialized_data.append(folio_report_dict)

        return json.dumps(serialized_data)

    def quantity(self, cashier_id, quantity):
        try:
            cashier = self.db.query(CashierModel).filter(CashierModel.id == cashier_id).first()

            if not cashier:
                return "Cajero no encontrado."
            
            cashier.available_folios = quantity
            cashier.updated_date = datetime.datetime.now(pytz.timezone('America/Santiago'))
            self.db.commit()
            return "Cantidad de folios actualizada."

        except Exception as e:
            # Captura cualquier error y retorna el mensaje de error
            error_message = str(e)
            return f"Error: {error_message}"
        

    def validate(self):
        try:
            folio_count = self.db.query(FolioModel).filter(FolioModel.requested_status_id == 0).count()
            
            if folio_count < 100:
                return 1  # Retorna 1 si hay menos de 100 folios
            else:
                return 0  # Retorna 0 si hay 100 o más folios
        
        except Exception as e:
            # Captura cualquier error y retorna el mensaje de error
            error_message = str(e)
            return f"Error: {error_message}"
        
    def assignation(self, folio, branch_office_id, cashier_id):
        try:
            # Consulta de folios disponibles
            folio_count = self.db.query(FolioModel).filter(FolioModel.folio == folio).filter(FolioModel.branch_office_id == branch_office_id).filter(FolioModel.cashier_id == cashier_id).count()
            
            # Valida si el conteo es menor a 100
            if folio_count > 0:
                return 1  # Retorna 1 si hay menos de 100 folios
            else:
                return 0  # Retorna 0 si hay 100 o más folios
        
        except Exception as e:
            # Captura cualquier error y retorna el mensaje de error
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get_folio(self, branch_office_id, cashier_id, requested_quantity, quantity_in_cashier):
        try:
            if requested_quantity > 0:
                # Consulta de cajero para obtener el folio_segment_id
                cashier = self.db.query(CashierModel).filter(CashierModel.id == cashier_id).first()

                if not cashier:
                    return "Cajero no encontrado."

                # Consulta para obtener el folio disponible (limitado a 1 folio)
                query = self.db.query(FolioModel).filter(FolioModel.requested_status_id == 0)

                if cashier.folio_segment_id == 0:
                    query = query.filter(FolioModel.folio_segment_id == 0)
                else:
                    query = query.filter(FolioModel.folio_segment_id == cashier.folio_segment_id)

                # Obtener un solo folio disponible
                folio = query.first()

                if not folio:
                    return "No hay folios disponibles con el estado solicitado."

                # Actualizar el folio directamente
                folio.branch_office_id = branch_office_id
                folio.cashier_id = cashier_id
                folio.requested_status_id = 1

                # Confirmar los cambios en la base de datos
                self.db.commit()

                # Serialización del folio actualizado
                folio_dict = {
                    "id": folio.id,
                    "folio": folio.folio,
                    "branch_office_id": folio.branch_office_id,
                    "cashier_id": folio.cashier_id,
                    "requested_status_id": folio.requested_status_id,
                }

                return json.dumps(folio_dict)
            else:
                return "La cantidad solicitada debe ser mayor a 0."
        except Exception as e:
            # Captura cualquier error y retorna el mensaje de error
            return f"Error: {str(e)}"
    
    def validate_caf_limit(self, folio_segment_id):
        try:

            if folio_segment_id != 9:
                settings = SettingClass(self.db).get()
                if settings:
                    folios = self.db.query(FolioModel).filter(FolioModel.requested_status_id == 0).filter(FolioModel.folio_segment_id == folio_segment_id).count()
                    caf_limit = settings['setting_data']['caf_limit']

                    if folios < caf_limit:
                        return 1
                    else:
                        return 0
                else:
                    return 3
            else:
                return 0
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get(self, branch_office_id, cashier_id, requested_quantity, quantity_in_cashier):
        try:
            cashier = self.db.query(CashierModel).filter(CashierModel.id == cashier_id).limit(1).first()
            cashier.available_folios = quantity_in_cashier
            self.db.add(cashier)
            self.db.commit()
            
            if requested_quantity > 0:
                response_validate_caf_limit = self.validate_caf_limit(cashier.folio_segment_id)

                if response_validate_caf_limit == 1:
                    AlertClass(self.db).send_email(1, cashier.folio_segment_id)

                folios = self.db.query(FolioModel).filter(FolioModel.requested_status_id == 0).filter(FolioModel.folio_segment_id == cashier.folio_segment_id).limit(1).all()

                # Verifica si hay folios disponibles
                if not folios:
                    return "No hay folios disponibles con el estado solicitado."

                # Procesa cada folio y actualiza sus valores
                for folio in folios:
                    folio.branch_office_id = branch_office_id
                    folio.cashier_id = cashier_id
                    folio.requested_status_id = 1
                    tz = pytz.timezone('America/Santiago')
                    current_date = datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                    folio.updated_date = current_date
                    self.db.add(folio)
                
                # Confirma todos los cambios después de procesar los folios
                self.db.commit()
                
                # Serialización de los folios actualizados
                serialized_data = []
                for folio in folios:
                    folio_dict = {
                        "id": folio.id,
                        "folio": folio.folio,
                        "branch_office_id": folio.branch_office_id,
                        "cashier_id": folio.cashier_id,
                        "requested_status_id": folio.requested_status_id,
                        # Agrega otros campos necesarios según el modelo FolioModel
                    }
                    serialized_data.append(folio_dict)
                
                return json.dumps(serialized_data)
            else:
                return "La cantidad solicitada debe ser mayor a 0."
        
        except Exception as e:
            # Captura cualquier error y retorna el mensaje de error
            error_message = str(e)
            return f"Error: {error_message}"

    def update(self, folio):
        folio_count = self.db.query(FolioModel).filter(FolioModel.folio == folio).count()
        if folio_count > 0:
            folio = self.db.query(FolioModel).filter(FolioModel.folio == folio).first()
            folio.used_status_id = 1
            self.db.add(folio)
            self.db.commit()

            return "Folio updated successfully"
        else:
            return "Folio not found"

    def update_billed_ticket(self, folio):
        folio_record = self.db.query(FolioModel).filter(FolioModel.folio == folio).first()
        
        if folio_record:
            folio_record.billed_status_id = 1
            self.db.commit()
            return f"Folio {folio} updated successfully"
        
        return "Folio not found"

    def request(self, amount):
        payload = {
            "credenciales": {
                "rutEmisor": "76063822-6",
                "nombreSucursal": "Casa Matriz"   
            },
            "codigoTipoDte": 39,
            "ambiente": 1
        }

        headers = {
            'Authorization': 'Basic cm9kcmlnb2NhYmV6YXNAamlzcGFya2luZy5jb206Um9ybzIwMjQu',
            'Content-Type': 'application/json'
        }

        response = requests.post(
            'https://api.simplefactura.cl/folios/consultar',
            data=json.dumps(payload),
            headers=headers
        )

        response_data = response.json()

        if response_data.get('status') == 200:
            data = response_data.get('data')

            quantity = len(data)

            if quantity > 0:
                folio_data = self.db.query(FolioModel).order_by(FolioModel.id.desc()).first()

                last_row = data[-1]

                available_caf_folios = last_row['hasta'] - folio_data.folio

                print(available_caf_folios)

                if available_caf_folios >= amount:
                    last_registered_folio = folio_data.folio
                    last_registered_folio += 1
                    for i in range(last_registered_folio, last_registered_folio + 1):
                        print(i)
                else:
                    return "No hay folios disponibles en el CAF"

    ALLOWED_DOCUMENT_TYPE_IDS = (33, 39, 61)
    FOLIO_DOC_TYPE_LABELS = {
        33: "Facturas",
        39: "Boletas",
        61: "Notas de Crédito",
    }

    def _no_folios_pool_message(self, document_type_id: int) -> str:
        label = self.FOLIO_DOC_TYPE_LABELS.get(int(document_type_id), "documentos")
        return f"No hay más folios para {label}"

    def reserve_next_by_document_type(
        self, document_type_id: int, branch_office_id: int, dte_id=None
    ):
        """
        Reserva folio libre de la pool central (branch_office_id=0, used_id=0).
        Tabla `folios`: document_type_id 33 (factura), 39 (boleta), 61 (nota de crédito).
        Asigna branch_office_id de la sucursal y used_id=1.
        """
        doc_type = int(document_type_id)
        if doc_type not in self.ALLOWED_DOCUMENT_TYPE_IDS:
            return {
                "status": "error",
                "message": "document_type_id debe ser 33 (factura), 39 (boleta) o 61 (nota de crédito)",
            }

        try:
            branch_id = int(branch_office_id)
        except (TypeError, ValueError):
            return {"status": "error", "message": "branch_office_id es requerido"}
        if branch_id <= 0:
            return {"status": "error", "message": "branch_office_id inválido"}

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dte_id_value = 0
        if dte_id not in (None, "", 0, "0"):
            try:
                dte_id_value = int(dte_id)
            except (TypeError, ValueError):
                dte_id_value = 0

        try:
            row = (
                self.db.execute(
                    text(
                        """
                        SELECT id, folio
                        FROM folios
                        WHERE document_type_id = :document_type_id
                          AND used_id = 0
                          AND branch_office_id = 0
                          AND (dte_id IS NULL OR dte_id = 0)
                        ORDER BY folio ASC
                        LIMIT 1
                        FOR UPDATE
                        """
                    ),
                    {"document_type_id": doc_type},
                )
                .mappings()
                .first()
            )
            if not row:
                return {
                    "status": "error",
                    "message": self._no_folios_pool_message(doc_type),
                }

            folio_id = int(row["id"])
            folio_number = int(row["folio"])
            updated = self.db.execute(
                text(
                    """
                    UPDATE folios
                    SET branch_office_id = :branch_office_id,
                        used_id = 1,
                        dte_id = :dte_id,
                        updated_date = :updated_date
                    WHERE id = :id
                      AND used_id = 0
                      AND branch_office_id = 0
                    """
                ),
                {
                    "id": folio_id,
                    "branch_office_id": branch_id,
                    "dte_id": dte_id_value,
                    "updated_date": now,
                },
            )
            if not updated.rowcount:
                self.db.rollback()
                return {
                    "status": "error",
                    "message": "El folio fue tomado por otra petición, intente de nuevo",
                }

            self.db.commit()
            return {
                "status": "success",
                "id": folio_id,
                "folio": folio_number,
                "dte_id": dte_id_value,
                "branch_office_id": branch_id,
                "document_type_id": doc_type,
            }
        except Exception as exc:
            self.db.rollback()
            return {"status": "error", "message": str(exc)}

    def bind_folio_to_dte(self, folio_row_id: int, dte_id: int, branch_office_id=None):
        """Vincula fila en folios al DTE emitido y asegura used_id=1."""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            params = {
                "id": int(folio_row_id),
                "dte_id": int(dte_id),
                "updated_date": now,
                "branch_office_id": int(branch_office_id) if branch_office_id not in (None, "", 0) else None,
            }
            if params["branch_office_id"]:
                sql = """
                    UPDATE folios
                    SET dte_id = :dte_id,
                        used_id = 1,
                        branch_office_id = :branch_office_id,
                        updated_date = :updated_date
                    WHERE id = :id
                """
            else:
                sql = """
                    UPDATE folios
                    SET dte_id = :dte_id,
                        used_id = 1,
                        updated_date = :updated_date
                    WHERE id = :id
                """
            self.db.execute(text(sql), params)
            self.db.commit()
            return {"status": "success"}
        except Exception as exc:
            self.db.rollback()
            return {"status": "error", "message": str(exc)}

    def mark_folio_used(self, folio_row_id: int, dte_id: int = 0, branch_office_id=None):
        """Marca folio como usado (used_id=1) sin liberarlo a la pool."""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            params = {
                "id": int(folio_row_id),
                "dte_id": int(dte_id or 0),
                "updated_date": now,
                "branch_office_id": int(branch_office_id) if branch_office_id not in (None, "", 0) else None,
            }
            if params["branch_office_id"]:
                sql = """
                    UPDATE folios
                    SET used_id = 1,
                        dte_id = CASE WHEN :dte_id > 0 THEN :dte_id ELSE dte_id END,
                        branch_office_id = :branch_office_id,
                        updated_date = :updated_date
                    WHERE id = :id
                """
            else:
                sql = """
                    UPDATE folios
                    SET used_id = 1,
                        dte_id = CASE WHEN :dte_id > 0 THEN :dte_id ELSE dte_id END,
                        updated_date = :updated_date
                    WHERE id = :id
                """
            self.db.execute(text(sql), params)
            self.db.commit()
            return {"status": "success"}
        except Exception as exc:
            self.db.rollback()
            return {"status": "error", "message": str(exc)}

    def _sf_emit_error_indicates_folio_consumed(self, emit_result, folio_number, dte_type_id=39) -> bool:
        """True si SimpleFactura ya tiene ese folio (no liberar a la pool)."""
        if not emit_result or emit_result.get("status") == "success":
            return False
        parts = []
        if emit_result.get("message"):
            parts.append(str(emit_result["message"]))
        for err in emit_result.get("errors") or []:
            parts.append(str(err))
        text_blob = " ".join(parts).lower()
        folio_s = str(int(folio_number))
        if "consumo existente" in text_blob:
            return True
        if "ya existe" in text_blob and folio_s in text_blob:
            return True
        if "ya existe un dte con folio" in text_blob:
            return True
        try:
            from app.backend.classes.customer_ticket_class import CustomerTicketClass

            pdf = CustomerTicketClass(self.db).save_simplefactura_pdf_ticket(
                int(folio_number), dte_type_id=int(dte_type_id)
            )
            return pdf.get("status") == "success"
        except Exception:
            return False

    def release_folio_pool_after_failed_emit(
        self,
        folio_row_id: int,
        *,
        folio_number: int,
        dte_type_id: int,
        emit_result=None,
        dte_id=None,
        branch_office_id=None,
    ):
        """
        Libera folio solo si la emisión falló y SF no consumió el número.
        Si SF ya emitió (ej. error duplicado), marca used_id=1.
        """
        if self._sf_emit_error_indicates_folio_consumed(emit_result, folio_number, dte_type_id):
            print(
                f"[folios] folio {folio_number} ya existe en SF; se marca used_id=1 (no liberar)",
                flush=True,
            )
            return self.mark_folio_used(folio_row_id, dte_id or 0, branch_office_id)
        return self.release_folio_pool(folio_row_id)

    def release_folio_pool(self, folio_row_id: int):
        """Libera folio si la emisión falló: branch_office_id→0, used_id→0, dte_id→0."""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.db.execute(
                text(
                    """
                    UPDATE folios
                    SET branch_office_id = 0,
                        used_id = 0,
                        dte_id = 0,
                        updated_date = :updated_date
                    WHERE id = :id
                    """
                ),
                {"id": int(folio_row_id), "updated_date": now},
            )
            self.db.commit()
            return {"status": "success", "message": "Folio liberado"}
        except Exception as exc:
            self.db.rollback()
            return {"status": "error", "message": str(exc)}

    # --- Asignación desde CAF SimpleFactura (DB1 Intrajis / DB2 máquinas) ---

    def _fetch_simplefactura_bearer_token(self) -> str:
        response = requests.get(JISBACKEND_SETTINGS_TOKEN_URL, timeout=15)
        if response.status_code != 200:
            raise ValueError(
                f"jisbackend get_token HTTP {response.status_code}: {(response.text or '')[:200]}"
            )
        body = response.json()
        message = body.get("message")
        if not isinstance(message, dict):
            raise ValueError("jisbackend get_token: respuesta sin message")
        token = message.get("simplefactura_token")
        if not token:
            raise ValueError("jisbackend get_token: simplefactura_token vacío")
        return token

    def fetch_simplefactura_cafs(self, dte_type_id: int = 39):
        """
        Lista CAF de boletas/facturas/NC desde SimpleFactura.
        Endpoint: POST /folios/consultar
        """
        token = self._fetch_simplefactura_bearer_token()
        payload = {
            "credenciales": {
                "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
                "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
            },
            "codigoTipoDte": int(dte_type_id),
            "ambiente": 1,
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            "https://api.simplefactura.cl/folios/consultar",
            json=payload,
            headers=headers,
            timeout=SF_FOLIOS_CONSULTAR_TIMEOUT,
        )
        if response.status_code == 401:
            token = self._fetch_simplefactura_bearer_token()
            headers["Authorization"] = f"Bearer {token}"
            response = requests.post(
                "https://api.simplefactura.cl/folios/consultar",
                json=payload,
                headers=headers,
                timeout=SF_FOLIOS_CONSULTAR_TIMEOUT,
            )
        if response.status_code != 200:
            raise ValueError(
                f"SimpleFactura folios/consultar HTTP {response.status_code}: "
                f"{(response.text or '')[:400]}"
            )
        body = response.json() if response.text else {}
        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, list):
            raise ValueError("SimpleFactura folios/consultar: respuesta sin lista de CAF")

        cafs = []
        for row in data:
            if not isinstance(row, dict):
                continue
            try:
                desde = int(row.get("desde"))
                hasta = int(row.get("hasta"))
            except (TypeError, ValueError):
                continue
            if desde <= 0 or hasta < desde:
                continue
            cafs.append(
                {
                    "desde": desde,
                    "hasta": hasta,
                    "folios_disponibles_sf": int(row.get("foliosDisponibles") or 0),
                    "fecha_ingreso": row.get("fechaIngreso"),
                    "fecha_vencimiento": row.get("fechaVencimiento"),
                    "tipo_dte": row.get("tipoDte") or f"DTE {dte_type_id}",
                    "codigo_sii": int(row.get("codigoSii") or dte_type_id),
                }
            )

        # Más nuevos primero (fechaIngreso desc).
        cafs.sort(key=lambda item: item.get("fecha_ingreso") or "1970-01-01", reverse=True)
        return cafs

    @staticmethod
    def _free_blocks_from_used(desde: int, hasta: int, used_sorted: list[int], quantity_needed: int):
        """
        Arma bloques continuos libres dentro de [desde, hasta] saltando used_sorted.
        Detiene al completar quantity_needed.
        """
        blocks = []
        taken = 0
        cursor = int(desde)
        end = int(hasta)
        used = [int(u) for u in used_sorted if int(desde) <= int(u) <= int(hasta)]

        def _push(block_from: int, block_to: int):
            nonlocal taken
            if block_to < block_from or taken >= quantity_needed:
                return
            available = block_to - block_from + 1
            need = quantity_needed - taken
            use = min(available, need)
            real_to = block_from + use - 1
            blocks.append(
                {
                    "desde": block_from,
                    "hasta": real_to,
                    "cantidad": use,
                }
            )
            taken += use

        for folio in used:
            if folio > cursor:
                _push(cursor, folio - 1)
                if taken >= quantity_needed:
                    return blocks, taken
            cursor = max(cursor, folio + 1)
        if cursor <= end and taken < quantity_needed:
            _push(cursor, end)
        return blocks, taken

    def _existing_folios_in_range(self, db_session, desde: int, hasta: int, *, document_type_id=None):
        """Folios ya cargados en una BD dentro del rango (ordenados, únicos)."""
        if document_type_id is not None:
            rows = db_session.execute(
                text(
                    """
                    SELECT DISTINCT folio AS folio
                    FROM folios
                    WHERE document_type_id = :doc_type
                      AND folio BETWEEN :desde AND :hasta
                    ORDER BY folio ASC
                    """
                ),
                {"doc_type": int(document_type_id), "desde": int(desde), "hasta": int(hasta)},
            ).mappings().all()
        else:
            rows = db_session.execute(
                text(
                    """
                    SELECT DISTINCT folio AS folio
                    FROM folios
                    WHERE folio BETWEEN :desde AND :hasta
                    ORDER BY folio ASC
                    """
                ),
                {"desde": int(desde), "hasta": int(hasta)},
            ).mappings().all()
        return [int(r["folio"]) for r in rows]

    def build_folio_allocation(
        self,
        quantity: int,
        *,
        db2=None,
        dte_type_id: int = 39,
        destination: str = "db2",
    ):
        """
        Calcula bloques libres por CAF cruzando DB1 + DB2.
        destination solo afecta el resumen (quién recibirá la carga).
        """
        quantity = int(quantity)
        if quantity <= 0:
            return {
                "status": "error",
                "message": "quantity debe ser mayor que 0",
            }

        try:
            cafs = self.fetch_simplefactura_cafs(dte_type_id)
        except (ValueError, requests.RequestException) as exc:
            return {"status": "error", "message": str(exc)}

        # Boletas: nunca asignar bajo el piso (CAFs viejos con consumo fantasma).
        floor = FOLIO_ALLOCATION_MIN_39 if int(dte_type_id) == 39 else 0

        remaining = quantity
        caf_allocations = []
        total_assignable = 0

        for caf in cafs:
            if remaining <= 0:
                break
            desde, hasta = caf["desde"], caf["hasta"]
            if hasta < floor:
                continue
            desde = max(desde, floor)
            used_db1 = self._existing_folios_in_range(
                self.db, desde, hasta, document_type_id=dte_type_id
            )
            used_db2 = []
            # DB2 solo almacena folios de boleta (39); para otros tipos el folio
            # es una serie SII independiente y no debe cruzarse contra máquinas.
            if db2 is not None and int(dte_type_id) == 39:
                used_db2 = self._existing_folios_in_range(db2, desde, hasta)
            used_merged = sorted(set(used_db1) | set(used_db2))
            blocks, taken = self._free_blocks_from_used(desde, hasta, used_merged, remaining)
            if not blocks:
                continue
            existing_count = len(used_merged)
            libres_antes = (hasta - desde + 1) - existing_count
            caf_allocations.append(
                {
                    "caf_desde": desde,
                    "caf_hasta": hasta,
                    "fecha_ingreso": caf.get("fecha_ingreso"),
                    "fecha_vencimiento": caf.get("fecha_vencimiento"),
                    "existentes_db1": len(used_db1),
                    "existentes_db2": len(used_db2),
                    "existentes_total": existing_count,
                    "blocks": blocks,
                    "cantidad": taken,
                    "libres_caf_antes": libres_antes,
                    "libres_caf_despues": libres_antes - taken,
                }
            )
            total_assignable += taken
            remaining -= taken

        warning = None
        if total_assignable < quantity:
            if int(dte_type_id) == 39 and floor > 0 and total_assignable == 0:
                warning = (
                    f"No hay folios libres desde el piso {floor:,} hacia arriba "
                    f"(CAF nuevo agotado en DB1+DB2). Pide un CAF en SimpleFactura "
                    f"que empiece sobre {floor - 1:,} y vuelve a previsualizar. "
                    f"Se solicitaron {quantity}."
                ).replace(",", ".")
            else:
                warning = (
                    f"Solo hay {total_assignable} folios libres en los CAF de SimpleFactura "
                    f"(cruzando DB1+DB2"
                    + (f", piso boleta {floor:,}".replace(",", ".") if floor else "")
                    + f"). Se solicitaron {quantity}."
                )
        elif any(len(a["blocks"]) > 1 for a in caf_allocations):
            warning = (
                "Algunos CAF tienen gaps (folios ya cargados en DB1/DB2); "
                "se tomaron bloques discontinuos."
            )

        return {
            "status": "success",
            "destination": destination,
            "dte_type_id": int(dte_type_id),
            "requested": quantity,
            "assignable": total_assignable,
            "shortfall": max(0, quantity - total_assignable),
            "allocation_floor": floor if int(dte_type_id) == 39 else None,
            "cafs": caf_allocations,
            "caf_remaining_after": sum(
                int(a.get("libres_caf_despues") or 0) for a in caf_allocations
            ),
            "warning": warning,
        }

    def confirm_folio_allocation(
        self,
        quantity: int,
        *,
        destination: str,
        folio_segment_id=None,
        db2=None,
        dte_type_id: int = 39,
    ):
        """
        Recalcula la asignación e inserta en DB1 (Intrajis) o DB2 (máquinas).
        """
        destination = (destination or "").strip().lower()
        if destination not in ("db1", "db2"):
            return {"status": "error", "message": "destination debe ser db1 o db2"}
        if destination == "db2":
            if db2 is None:
                return {"status": "error", "message": "DB2 no disponible"}
            try:
                segment_id = int(folio_segment_id)
            except (TypeError, ValueError):
                return {"status": "error", "message": "Seleccione un segmento"}
            if segment_id not in (1, 2, 3):
                return {"status": "error", "message": "Segmento debe ser 1, 2 o 3"}
        else:
            segment_id = None

        plan = self.build_folio_allocation(
            quantity,
            db2=db2,
            dte_type_id=dte_type_id,
            destination=destination,
        )
        if plan.get("status") != "success":
            return plan

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        folio_numbers = []
        for caf in plan.get("cafs") or []:
            for block in caf.get("blocks") or []:
                folio_numbers.extend(range(int(block["desde"]), int(block["hasta"]) + 1))

        inserted = 0
        try:
            if destination == "db1":
                insert_sql = text(
                    """
                    INSERT IGNORE INTO folios (
                        folio, dte_id, used_id, document_type_id, branch_office_id,
                        added_date, updated_date
                    ) VALUES (
                        :folio, 0, 0, :document_type_id, 0,
                        :added_date, :updated_date
                    )
                    """
                )
                rows = [
                    {
                        "folio": folio,
                        "document_type_id": int(dte_type_id),
                        "added_date": now,
                        "updated_date": now,
                    }
                    for folio in folio_numbers
                ]
                for offset in range(0, len(rows), 1000):
                    result = self.db.execute(insert_sql, rows[offset : offset + 1000])
                    if result.rowcount and result.rowcount > 0:
                        inserted += int(result.rowcount)
                self.db.commit()
            else:
                insert_sql = text(
                    """
                    INSERT IGNORE INTO folios (
                        folio, branch_office_id, cashier_id, folio_segment_id,
                        requested_status_id, used_status_id, billed_status_id,
                        added_date, updated_date
                    ) VALUES (
                        :folio, 0, 0, :folio_segment_id,
                        0, 0, 0,
                        :added_date, :updated_date
                    )
                    """
                )
                rows = [
                    {
                        "folio": folio,
                        "folio_segment_id": int(segment_id),
                        "added_date": now,
                        "updated_date": now,
                    }
                    for folio in folio_numbers
                ]
                for offset in range(0, len(rows), 1000):
                    result = db2.execute(insert_sql, rows[offset : offset + 1000])
                    if result.rowcount and result.rowcount > 0:
                        inserted += int(result.rowcount)
                db2.commit()
        except Exception as exc:
            if destination == "db1":
                self.db.rollback()
            elif db2 is not None:
                db2.rollback()
            return {"status": "error", "message": str(exc)}

        requested = int(plan["requested"])
        skipped = max(0, requested - inserted)
        warning = plan.get("warning")
        if skipped and inserted:
            warning = (
                f"Se solicitaron {requested}, se cargaron {inserted} y se omitieron {skipped} "
                f"(ya existían o no había más libres en CAF)."
            )
        elif skipped and not inserted:
            warning = (
                f"No se cargó ningún folio. Solicitados: {requested}. "
                f"Revisa CAFs libres y choques con DB1/DB2."
            )

        return {
            "status": "success",
            "message": "OK",
            "destination": destination,
            "folio_segment_id": segment_id,
            "dte_type_id": int(dte_type_id),
            "requested": requested,
            "inserted": inserted,
            "skipped_existing": skipped,
            "assignable": plan.get("assignable"),
            "cafs": plan.get("cafs"),
            "caf_remaining_after": plan.get("caf_remaining_after"),
            "warning": warning,
        }