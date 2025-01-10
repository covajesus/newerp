from app.backend.db.models import FolioModel
import json

class CafClass:
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