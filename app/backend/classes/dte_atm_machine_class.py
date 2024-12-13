from app.backend.db.models import DteAtmMachineModel
from datetime import datetime

class DteAtmMachineClass:
    def __init__(self, db):
        self.db = db


    def store(self, dte_atm_inputs):
        dte_atm_machine = DteAtmMachineModel(
            branch_office_id=dte_atm_inputs['branch_office_id'],
            cashier_id=dte_atm_inputs['cashier_id'],
            dte_type_id=dte_atm_inputs['dte_type_id'],
            sii_send_status_id=dte_atm_inputs['sii_send_status_id'],
            sii_status_id=dte_atm_inputs['sii_status_id'],
            sii_track_id=dte_atm_inputs['sii_track_id'],
            dte_code=dte_atm_inputs['dte_code'],
            folio=dte_atm_inputs['folio'],
            cash_amount=dte_atm_inputs['cash_amount'],
            card_amount=dte_atm_inputs['card_amount'],
            subtotal=dte_atm_inputs['subtotal'],
            tax=dte_atm_inputs['tax'],
            discount=dte_atm_inputs['discount'],
            total=dte_atm_inputs['total'],
            ticket_serial_number=dte_atm_inputs['ticket_serial_number'],
            ticket_hour=dte_atm_inputs['ticket_hour'],
            ticket_transaction_number=dte_atm_inputs['ticket_transaction_number'],
            ticket_dispenser_number=dte_atm_inputs['ticket_dispenser_number'],
            ticket_number=dte_atm_inputs['ticket_number'],
            ticket_station_number=dte_atm_inputs['ticket_station_number'],
            ticket_sa=dte_atm_inputs['ticket_sa'],
            ticket_correlative=dte_atm_inputs['ticket_correlative'],
            entrance_hour=dte_atm_inputs['entrance_hour'],
            exit_hour=dte_atm_inputs['exit_hour'],
            item_quantity=dte_atm_inputs['item_quantity'],
            sii_date=dte_atm_inputs['sii_date'],
            added_date=datetime.now()
        )

        self.db.add(dte_atm_machine)

        try:
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
