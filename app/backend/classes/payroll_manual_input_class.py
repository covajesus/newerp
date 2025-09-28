from app.backend.db.models import PayrollManualInputModel
from app.backend.classes.payroll_class import PayrollClass
from app.backend.classes.payroll_item_value_class import PayrollItemValueClass
from app.backend.classes.helper_class import HelperClass
from datetime import datetime

class PayrollManualInputClass:
    def __init__(self, db):
        self.db = db

    def store(self, manual_inputs_list):
        for payroll_manual_input in manual_inputs_list.payroll_employees:
            rut = payroll_manual_input.rut
            payroll_item_id = payroll_manual_input.payroll_item_id
            amount = payroll_manual_input.amount
            period = payroll_manual_input.period

            payroll_item_value_data = {}
            payroll_item_value_data['item_id'] = payroll_item_id
            payroll_item_value_data['rut'] = rut
            payroll_item_value_data['period'] = period
            payroll_item_value_data['amount'] = amount

            existence_status = PayrollItemValueClass(self.db).existence(rut, payroll_item_id, period)

            if existence_status > 0 and existence_status != None:
                payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, payroll_item_id, period)

                if payroll_item_value.amount != amount:
                    if amount == 0 or amount == None:
                        PayrollItemValueClass(self.db).delete_with_period(rut, payroll_item_id, period)
                    else:
                        PayrollItemValueClass(self.db).update(payroll_item_value_data)
            else:
                if amount != 0 and amount != None and amount != '0' and amount != '':
                    PayrollItemValueClass(self.db).store(payroll_item_value_data)

        return 1
    
    def multiple_store(self, payroll_manual_inputs):
        numeric_rut = HelperClass().numeric_rut(str(payroll_manual_inputs.rut))

        existence_status = PayrollItemValueClass(self.db).existence(numeric_rut, payroll_manual_inputs.payroll_item_id, payroll_manual_inputs.period)

        if existence_status > 0 and existence_status != None:
            PayrollItemValueClass(self.db).delete_with_period(numeric_rut, payroll_manual_inputs.payroll_item_id, payroll_manual_inputs.period)

            payroll_item_value_data = {}
            payroll_item_value_data['item_id'] = payroll_manual_inputs.payroll_item_id
            payroll_item_value_data['rut'] = numeric_rut
            payroll_item_value_data['period'] = payroll_manual_inputs.period
            payroll_item_value_data['amount'] = payroll_manual_inputs.amount

            PayrollItemValueClass(self.db).store(payroll_item_value_data)
        else:
            payroll_item_value_data = {}
            payroll_item_value_data['item_id'] = payroll_manual_inputs.payroll_item_id
            payroll_item_value_data['rut'] = numeric_rut
            payroll_item_value_data['period'] = payroll_manual_inputs.period
            payroll_item_value_data['amount'] = payroll_manual_inputs.amount

            PayrollItemValueClass(self.db).store(payroll_item_value_data)

        return 1