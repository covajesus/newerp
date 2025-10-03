from app.backend.db.models import FolioModel, CashierModel
import json
from fastapi.responses import Response
from sqlalchemy import text

class CafClass:
    def __init__(self, db, db2=None):
        self.db = db
        self.db2 = db2

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
                        "billed_status_id": folio.billed_status_id,
                        "requested_status_id": folio.requested_status_id,
                        "used_status_id": folio.used_status_id,
                    } for folio in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def manual(self, branch_office_id, cashier_id, quantity):
        """
        Crear CAF manual: seleccionar folios disponibles, actualizarlos y generar archivo SQL
        """
        try:
            # Paso 0: Obtener el folio_segment_id del cashier
            cashier = self.db2.query(CashierModel).filter(CashierModel.id == cashier_id).first()
            if not cashier:
                return {"status": "error", "message": f"Cashier with ID {cashier_id} not found"}
            
            folio_segment_id = cashier.folio_segment_id
            if not folio_segment_id:
                return {"status": "error", "message": f"Cashier {cashier_id} does not have a folio_segment_id assigned"}
            
            # Paso 1: Seleccionar folios disponibles
            select_query = text("""
                SELECT 0 as used_id, folio 
                FROM folios 
                WHERE folio_segment_id = :folio_segment_id 
                AND cashier_id = 0 
                AND requested_status_id = 0 
                ORDER BY id DESC 
                LIMIT :quantity
            """)
            
            result = self.db2.execute(select_query, {
                "folio_segment_id": folio_segment_id,
                "quantity": quantity
            })
            folios_data = result.fetchall()
            
            if not folios_data:
                return {"status": "error", "message": f"No hay folios disponibles para el segment {folio_segment_id}"}
            
            if len(folios_data) < quantity:
                return {"status": "error", "message": f"Solo hay {len(folios_data)} folios disponibles para el segment {folio_segment_id}, se solicitaron {quantity}"}
            
            # Obtener el rango de folios (desde el menor hasta el mayor)
            folios_numbers = [row.folio for row in folios_data]
            folio_min = min(folios_numbers)
            folio_max = max(folios_numbers)
            
            # Paso 2: Actualizar los folios seleccionados
            from datetime import datetime
            current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            update_query = text("""
                UPDATE folios 
                SET cashier_id = :cashier_id, 
                    branch_office_id = :branch_office_id, 
                    requested_status_id = 1,
                    added_date = :added_date,
                    updated_date = :updated_date
                WHERE folio <= :folio_max 
                AND folio >= :folio_min
                AND folio_segment_id = :folio_segment_id 
                AND cashier_id = 0 
                AND requested_status_id = 0
            """)
            
            self.db2.execute(update_query, {
                "cashier_id": cashier_id,
                "branch_office_id": branch_office_id,
                "folio_max": folio_max,
                "folio_min": folio_min,
                "folio_segment_id": folio_segment_id,
                "added_date": current_datetime,
                "updated_date": current_datetime
            })
            
            self.db2.commit()
            
            # Paso 3: Generar contenido del archivo SQL
            sql_content = "-- CAF Manual Generated SQL\n"
            sql_content += f"-- Range: {folio_min} to {folio_max}\n"
            sql_content += f"-- Quantity: {quantity}\n"
            sql_content += f"-- Branch Office ID: {branch_office_id}\n"
            sql_content += f"-- Cashier ID: {cashier_id}\n"
            sql_content += f"-- Folio Segment ID: {folio_segment_id}\n"
            sql_content += f"-- Generated Date: {current_datetime}\n\n"
            
            for folio_number in sorted(folios_numbers):
                sql_content += f"INSERT INTO folios (used_id, folio, added_date, updated_date) VALUES (0, {folio_number}, '{current_datetime}', '{current_datetime}');\n"
            
            return {
                "status": "success",
                "message": f"CAF manual creado exitosamente. Folios del {folio_min} al {folio_max} para segment {folio_segment_id}",
                "data": {
                    "folios_assigned": len(folios_data),
                    "folio_min": folio_min,
                    "folio_max": folio_max,
                    "branch_office_id": branch_office_id,
                    "cashier_id": cashier_id,
                    "folio_segment_id": folio_segment_id,
                    "sql_content": sql_content
                }
            }
            
        except Exception as e:
            self.db2.rollback()
            return {"status": "error", "message": f"Error creating manual CAF: {str(e)}"}