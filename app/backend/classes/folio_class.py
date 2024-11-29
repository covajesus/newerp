from app.backend.db.models import FolioModel
import json

class FolioClass:
    def __init__(self, db):
        self.db = db

    # Funcion para obtener a todos los folios con paginacion
    def get_all(self, page=0, items_per_page=10):
        try:
            if page != 0:
                data_query = self.db.query(FolioModel.id, FolioModel.folio, FolioModel.branch_office_id, FolioModel.cashier_id, FolioModel.requested_status_id, FolioModel.used_status_id). \
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
                        "requested_status_id": folio.requested_status_id,
                        "used_status_id": folio.used_status_id,
                    } for folio in data]

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
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
        
    def validate(self):
        try:
            # Consulta de folios disponibles
            folio_count = self.db.query(FolioModel).filter(FolioModel.requested_status_id == 0).count()
            
            # Valida si el conteo es menor a 100
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

    def get(self, branch_office_id, cashier_id, requested_quantity, quantity_in_cashier):
        try:
            if requested_quantity > 0:
                # Consulta de folios disponibles con límite de cantidad especificada
                folios = self.db.query(FolioModel).filter(FolioModel.requested_status_id == 0).limit(1).all()
                
                # Verifica si hay folios disponibles
                if not folios:
                    return "No hay folios disponibles con el estado solicitado."

                # Procesa cada folio y actualiza sus valores
                for folio in folios:
                    folio.branch_office_id = branch_office_id
                    folio.cashier_id = cashier_id
                    folio.requested_status_id = 1
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
        folio_count = self.db.query(FolioModel).filter(FolioModel.folio == folio).count()
        if folio_count > 0:
            update_folio = self.db.query(FolioModel).filter(FolioModel.folio == folio).first()
            update_folio.billed_status_id = 1
            self.db.add(update_folio)
            self.db.commit()

            return "Folio "+ str(folio) +" updated successfully"
        else:
            return "Folio not found"