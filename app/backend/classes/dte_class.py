import requests
from datetime import datetime
from app.backend.db.models import DteModel

class DteClass:
    def __init__(self, db):
        self.db = db

    def get_total_quantity(user_inputs):

        if user_inputs['rol_id'] == 4 or user_inputs['rol_id'] == 5:
            user_inputs['rol_id'] = 1

        if user_inputs['rol_id'] == 3:
            user_inputs['rol_id'] = 4

        url = "https://jisparking.com/api/dte/receivable/"+ str(user_inputs['rol_id']) +"/"+ str(user_inputs['rut']) +"?api_token="+ str(user_inputs['api_token']) +""

        payload={}
        headers = {}

        response = requests.request("POST", url, headers=headers, data=payload)

        return response.text
    
    def get_total_amount(user_inputs):

        if user_inputs['rol_id'] == 4 or user_inputs['rol_id'] == 5:
            user_inputs['rol_id'] = 1

        if user_inputs['rol_id'] == 3:
            user_inputs['rol_id'] = 4
            
        url = "https://jisparking.com/api/dte/receivable/"+ str(user_inputs['rol_id']) +"/"+ str(user_inputs['rut']) +"?api_token="+ str(user_inputs['api_token']) +""

        payload={}
        headers = {}

        response = requests.request("POST", url, headers=headers, data=payload)

        return response.text
    
    def store(self, dte_inputs):
        dte = DteModel(
            branch_office_id=dte_inputs['branch_office_id'],
            cashier_id=dte_inputs['cashier_id'],
            dte_type_id=dte_inputs['dte_type_id'],
            folio=dte_inputs['folio'],
            cash_amount=dte_inputs['cash_amount'],
            card_amount=dte_inputs['card_amount'],
            subtotal=dte_inputs['subtotal'],
            tax=dte_inputs['tax'],
            discount=dte_inputs['discount'],
            total=dte_inputs['total'],
            ticket_serial_number=dte_inputs['ticket_serial_number'],
            ticket_hour=dte_inputs['ticket_hour'],
            ticket_transaction_number=dte_inputs['ticket_transaction_number'],
            ticket_dispenser_number=dte_inputs['ticket_dispenser_number'],
            ticket_number=dte_inputs['ticket_number'],
            ticket_station_number=dte_inputs['ticket_station_number'],
            ticket_sa=dte_inputs['ticket_sa'],
            ticket_correlative=dte_inputs['ticket_correlative'],
            entrance_hour=dte_inputs['entrance_hour'],
            exit_hour=dte_inputs['exit_hour'],
            added_date=dte_inputs['added_date']
        )

        self.db.add(dte)

        try:
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"