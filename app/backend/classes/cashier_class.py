from app.backend.db.models import CashierModel
from app.backend.db.models import LatestUpdateCashierModel
import json

class CashierClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, branch_office_id = ''):
        try:
            if branch_office_id == '':
                data = self.db.query(CashierModel).filter(CashierModel.folio_segment_id != 9).order_by(CashierModel.cashier).all()
            else :
                data = self.db.query(CashierModel).filter(CashierModel.branch_office_id == branch_office_id).filter(CashierModel.folio_segment_id != 9).order_by(CashierModel.cashier).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(CashierModel).filter(getattr(CashierModel, field) == value).order_by(CashierModel.cashier).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def get_subscriber_cashier(self, branch_office_id):
        try:
            data = self.db.query(CashierModel).filter(CashierModel.branch_office_id == branch_office_id).filter(CashierModel.folio_segment_id == 9).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
         
    def get_with_machine(self, id):
        try:
            data = self.db.query(CashierModel).filter(CashierModel.getaway_machine_id == 1). filter(CashierModel.branch_office_id == id).first()
            
            return data.id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def latest_update(self):
        cashier_reports = self.db.query(LatestUpdateCashierModel).all()

        if not cashier_reports:
            return "No hay cajaas en el informe."
        
        serialized_data = []
        for cashier_report in cashier_reports:
            cashier_report_dict = {
                "id": cashier_report.id,
                "cashier": cashier_report.cashier,
                "last_updated_date": cashier_report.last_updated_date.isoformat() if cashier_report.last_updated_date else None,
                "rustdesk": cashier_report.rustdesk,
                "anydesk": cashier_report.anydesk
            }
            serialized_data.append(cashier_report_dict)

        return json.dumps(serialized_data)