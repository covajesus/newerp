from app.backend.db.models import FolioModel
import json

class FolioClass:
    def __init__(self, db):
        self.db = db

    def get(self, branch_office_id, cashier_id, quantity):
        try:
            if quantity > 0:
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
        folio = self.db.query(FolioModel).filter(FolioModel.folio == folio).first()
        folio.used_status_id = 1
        self.db.add(folio)
        self.db.commit()

        return "Folio updated successfully"