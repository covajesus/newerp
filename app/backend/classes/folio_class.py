from app.backend.db.models import FolioModel

class FolioClass:
    def __init__(self, db):
        self.db = db

    def get(self, branch_office_id, cashier_id, quantity):
        try:
            folios = self.db.query(FolioModel).filter(FolioModel.requested_status_id == 0).limit(quantity).all()

            for folio in folios:
                folio =  self.db.query(FolioModel).filter(FolioModel.folio == folio.folio).first()
                folio.branch_office_id = branch_office_id
                folio.cashier_id = cashier_id
                folio.requested_status_id = 1
                self.db.add(folio)
                self.db.commit()

            return folios
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"