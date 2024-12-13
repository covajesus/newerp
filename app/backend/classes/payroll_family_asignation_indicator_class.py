from app.backend.db.models import PayrollFamilyAsignationIndicatorModel
from datetime import datetime
from app.backend.classes.helper_class import HelperClass

class PayrollFamilyAsignationIndicatorClass:
    def __init__(self, db):
        self.db = db

    def get(self, section_id, period):
        try:
            data = self.db.query(PayrollFamilyAsignationIndicatorModel).filter(PayrollFamilyAsignationIndicatorModel.section_id == section_id, PayrollFamilyAsignationIndicatorModel.period == period).first()

            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, section_id, payroll_indicator_inputs):
        try:
            if section_id == 1:
                a_family_assignment_amount = HelperClass().remove_from_string(".", payroll_indicator_inputs['a_family_assignment_amount'])
                a_family_assignment_amount = HelperClass().replace(",", ".", a_family_assignment_amount)
                a_family_assignment_rent_requirement_input_minimum_value = HelperClass().remove_from_string(".", payroll_indicator_inputs['a_family_assignment_rent_requirement_input_minimum_value'])
                a_family_assignment_rent_requirement_input_minimum_value = HelperClass().replace(",", ".", a_family_assignment_rent_requirement_input_minimum_value)
                a_family_assignment_rent_requirement_input_top_value = HelperClass().remove_from_string(".", payroll_indicator_inputs['a_family_assignment_rent_requirement_input_top_value'])
                a_family_assignment_rent_requirement_input_top_value = HelperClass().replace(",", ".", a_family_assignment_rent_requirement_input_top_value)

                payroll_family_asignation_indicator = PayrollFamilyAsignationIndicatorModel()
                payroll_family_asignation_indicator.section_id = section_id
                payroll_family_asignation_indicator.amount = a_family_assignment_amount
                payroll_family_asignation_indicator.minimum_value_rate = a_family_assignment_rent_requirement_input_minimum_value
                payroll_family_asignation_indicator.top_value_rate = a_family_assignment_rent_requirement_input_top_value
                payroll_family_asignation_indicator.period = payroll_indicator_inputs['period']
                payroll_family_asignation_indicator.added_date = datetime.now()
                self.db.add(payroll_family_asignation_indicator)
                self.db.commit()

            if section_id == 2:
                b_family_assignment_amount = HelperClass().remove_from_string(".", payroll_indicator_inputs['b_family_assignment_amount'])
                b_family_assignment_amount = HelperClass().replace(",", ".", b_family_assignment_amount)
                b_family_assignment_rent_requirement_input_minimum_value = HelperClass().remove_from_string(".", payroll_indicator_inputs['b_family_assignment_rent_requirement_input_minimum_value'])
                b_family_assignment_rent_requirement_input_minimum_value = HelperClass().replace(",", ".", b_family_assignment_rent_requirement_input_minimum_value)
                b_family_assignment_rent_requirement_input_top_value = HelperClass().remove_from_string(".", payroll_indicator_inputs['b_family_assignment_rent_requirement_input_top_value'])
                b_family_assignment_rent_requirement_input_top_value = HelperClass().replace(",", ".", b_family_assignment_rent_requirement_input_top_value)

                payroll_family_asignation_indicator = PayrollFamilyAsignationIndicatorModel()
                payroll_family_asignation_indicator.section_id = section_id
                payroll_family_asignation_indicator.amount = b_family_assignment_amount
                payroll_family_asignation_indicator.minimum_value_rate = b_family_assignment_rent_requirement_input_minimum_value
                payroll_family_asignation_indicator.top_value_rate = b_family_assignment_rent_requirement_input_top_value
                payroll_family_asignation_indicator.period = payroll_indicator_inputs['period']
                payroll_family_asignation_indicator.added_date = datetime.now()
                self.db.add(payroll_family_asignation_indicator)
                self.db.commit()

            if section_id == 3:
                c_family_assignment_amount = HelperClass().remove_from_string(".", payroll_indicator_inputs['c_family_assignment_amount'])
                c_family_assignment_amount = HelperClass().replace(",", ".", c_family_assignment_amount)
                c_family_assignment_rent_requirement_input_minimum_value = HelperClass().remove_from_string(".", payroll_indicator_inputs['c_family_assignment_rent_requirement_input_minimum_value'])
                c_family_assignment_rent_requirement_input_minimum_value = HelperClass().replace(",", ".", c_family_assignment_rent_requirement_input_minimum_value)
                c_family_assignment_rent_requirement_input_top_value = HelperClass().remove_from_string(".", payroll_indicator_inputs['c_family_assignment_rent_requirement_input_top_value'])
                c_family_assignment_rent_requirement_input_top_value = HelperClass().replace(",", ".", c_family_assignment_rent_requirement_input_top_value)


                payroll_family_asignation_indicator = PayrollFamilyAsignationIndicatorModel()
                payroll_family_asignation_indicator.section_id = section_id
                payroll_family_asignation_indicator.amount = c_family_assignment_amount
                payroll_family_asignation_indicator.minimum_value_rate = c_family_assignment_rent_requirement_input_minimum_value
                payroll_family_asignation_indicator.top_value_rate = c_family_assignment_rent_requirement_input_top_value
                payroll_family_asignation_indicator.period = payroll_indicator_inputs['period']
                payroll_family_asignation_indicator.added_date = datetime.now()
                self.db.add(payroll_family_asignation_indicator)
                self.db.commit()

            if section_id == 4:
                d_family_assignment_amount = HelperClass().remove_from_string(".", payroll_indicator_inputs['d_family_assignment_amount'])
                d_family_assignment_amount = HelperClass().replace(",", ".", d_family_assignment_amount)
                d_family_assignment_rent_requirement_input_minimum_value = HelperClass().remove_from_string(".", payroll_indicator_inputs['d_family_assignment_rent_requirement_input_minimum_value'])
                d_family_assignment_rent_requirement_input_minimum_value = HelperClass().replace(",", ".", d_family_assignment_rent_requirement_input_minimum_value)
                d_family_assignment_rent_requirement_input_top_value = HelperClass().remove_from_string(".", payroll_indicator_inputs['d_family_assignment_rent_requirement_input_top_value'])
                d_family_assignment_rent_requirement_input_top_value = HelperClass().replace(",", ".", d_family_assignment_rent_requirement_input_top_value)

                payroll_family_asignation_indicator = PayrollFamilyAsignationIndicatorModel()
                payroll_family_asignation_indicator.section_id = section_id
                payroll_family_asignation_indicator.amount = d_family_assignment_amount
                payroll_family_asignation_indicator.minimum_value_rate = d_family_assignment_rent_requirement_input_minimum_value
                payroll_family_asignation_indicator.top_value_rate = d_family_assignment_rent_requirement_input_top_value
                payroll_family_asignation_indicator.period = payroll_indicator_inputs['period']
                payroll_family_asignation_indicator.added_date = datetime.now()
                self.db.add(payroll_family_asignation_indicator)
                self.db.commit()

            inserted_id = payroll_family_asignation_indicator.id

            return inserted_id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"