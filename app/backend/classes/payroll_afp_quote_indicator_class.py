from app.backend.db.models import PayrollAfpQuoteIndicatorModel
from app.backend.classes.helper_class import HelperClass
from datetime import datetime

class PayrollAfpQuoteIndicatorClass:
    def __init__(self, db):
        self.db = db

    def get(self, pention_id, period):
        data = self.db.query(PayrollAfpQuoteIndicatorModel).filter(PayrollAfpQuoteIndicatorModel.pention_id == pention_id, PayrollAfpQuoteIndicatorModel.period == period).first()

        return data
    
    def store(self, pention_id, payroll_indicator_inputs):
        try:
            payroll_afp_quote_indicator = PayrollAfpQuoteIndicatorModel()

            if pention_id == 1:
                cuprum_dependent_rate_afp = HelperClass().remove_from_string(".", payroll_indicator_inputs['cuprum_dependent_rate_afp'])
                cuprum_dependent_rate_afp = HelperClass().replace(",", ".", cuprum_dependent_rate_afp)
                cuprum_dependent_sis = HelperClass().remove_from_string(".", payroll_indicator_inputs['cuprum_dependent_sis'])
                cuprum_dependent_sis = HelperClass().replace(",", ".", cuprum_dependent_sis)
                cuprum_independent_rate_afp = HelperClass().remove_from_string(".", payroll_indicator_inputs['cuprum_independent_rate_afp'])
                cuprum_independent_rate_afp = HelperClass().replace(",", ".", cuprum_independent_rate_afp)

                payroll_afp_quote_indicator = PayrollAfpQuoteIndicatorModel()
                payroll_afp_quote_indicator.pention_id = pention_id
                payroll_afp_quote_indicator.dependent_rate_afp = cuprum_dependent_rate_afp
                payroll_afp_quote_indicator.dependent_sis = cuprum_dependent_sis
                payroll_afp_quote_indicator.independent_rate_afp = cuprum_independent_rate_afp
                payroll_afp_quote_indicator.period = payroll_indicator_inputs['period']
                payroll_afp_quote_indicator.added_date = datetime.now()
                self.db.add(payroll_afp_quote_indicator)
                self.db.commit()

            if pention_id == 2:
                habitat_dependent_rate_afp = HelperClass().remove_from_string(".", payroll_indicator_inputs['habitat_dependent_rate_afp'])
                habitat_dependent_rate_afp = HelperClass().replace(",", ".", habitat_dependent_rate_afp)
                habitat_dependent_sis = HelperClass().remove_from_string(".", payroll_indicator_inputs['habitat_dependent_sis'])
                habitat_dependent_sis = HelperClass().replace(",", ".", habitat_dependent_sis)
                habitat_independent_rate_afp = HelperClass().remove_from_string(".", payroll_indicator_inputs['habitat_independent_rate_afp'])
                habitat_independent_rate_afp = HelperClass().replace(",", ".", habitat_independent_rate_afp)
                
                payroll_afp_quote_indicator = PayrollAfpQuoteIndicatorModel()
                payroll_afp_quote_indicator.pention_id = pention_id
                payroll_afp_quote_indicator.dependent_rate_afp = habitat_dependent_rate_afp
                payroll_afp_quote_indicator.dependent_sis = habitat_dependent_sis
                payroll_afp_quote_indicator.independent_rate_afp = habitat_independent_rate_afp
                payroll_afp_quote_indicator.period = payroll_indicator_inputs['period']
                payroll_afp_quote_indicator.added_date = datetime.now()
                self.db.add(payroll_afp_quote_indicator)
                self.db.commit()

            if pention_id == 3:
                planvital_dependent_rate_afp = HelperClass().remove_from_string(".", payroll_indicator_inputs['planvital_dependent_rate_afp'])
                planvital_dependent_rate_afp = HelperClass().replace(",", ".", planvital_dependent_rate_afp)
                planvital_dependent_sis = HelperClass().remove_from_string(".", payroll_indicator_inputs['planvital_dependent_sis'])
                planvital_dependent_sis = HelperClass().replace(",", ".", planvital_dependent_sis)
                planvital_independent_rate_afp = HelperClass().remove_from_string(".", payroll_indicator_inputs['planvital_independent_rate_afp'])
                planvital_independent_rate_afp = HelperClass().replace(",", ".", planvital_independent_rate_afp)

                payroll_afp_quote_indicator = PayrollAfpQuoteIndicatorModel()
                payroll_afp_quote_indicator.pention_id = pention_id
                payroll_afp_quote_indicator.dependent_rate_afp = planvital_dependent_rate_afp
                payroll_afp_quote_indicator.dependent_sis = planvital_dependent_sis
                payroll_afp_quote_indicator.independent_rate_afp = planvital_independent_rate_afp
                payroll_afp_quote_indicator.period = payroll_indicator_inputs['period']
                payroll_afp_quote_indicator.added_date = datetime.now()
                self.db.add(payroll_afp_quote_indicator)
                self.db.commit()

            if pention_id == 4:
                provida_dependent_rate_afp = HelperClass().remove_from_string(".", payroll_indicator_inputs['provida_dependent_rate_afp'])
                provida_dependent_rate_afp = HelperClass().replace(",", ".", provida_dependent_rate_afp)
                provida_dependent_sis = HelperClass().remove_from_string(".", payroll_indicator_inputs['provida_dependent_sis'])
                provida_dependent_sis = HelperClass().replace(",", ".", provida_dependent_sis)
                provida_independent_rate_afp = HelperClass().remove_from_string(".", payroll_indicator_inputs['provida_independent_rate_afp'])
                provida_independent_rate_afp = HelperClass().replace(",", ".", provida_independent_rate_afp)

                payroll_afp_quote_indicator = PayrollAfpQuoteIndicatorModel()
                payroll_afp_quote_indicator.pention_id = pention_id
                payroll_afp_quote_indicator.dependent_rate_afp = provida_dependent_rate_afp
                payroll_afp_quote_indicator.dependent_sis = provida_dependent_sis
                payroll_afp_quote_indicator.independent_rate_afp = provida_independent_rate_afp
                payroll_afp_quote_indicator.period = payroll_indicator_inputs['period']
                payroll_afp_quote_indicator.added_date = datetime.now()
                self.db.add(payroll_afp_quote_indicator)
                self.db.commit()

            if pention_id == 5:
                capital_dependent_rate_afp = HelperClass().remove_from_string(".", payroll_indicator_inputs['capital_dependent_rate_afp'])
                capital_dependent_rate_afp = HelperClass().replace(",", ".", capital_dependent_rate_afp)
                capital_dependent_sis = HelperClass().remove_from_string(".", payroll_indicator_inputs['capital_dependent_sis'])
                capital_dependent_sis = HelperClass().replace(",", ".", capital_dependent_sis)
                capital_independent_rate_afp = HelperClass().remove_from_string(".", payroll_indicator_inputs['capital_independent_rate_afp'])
                capital_independent_rate_afp = HelperClass().replace(",", ".", capital_independent_rate_afp)

                payroll_afp_quote_indicator = PayrollAfpQuoteIndicatorModel()
                payroll_afp_quote_indicator.pention_id = pention_id
                payroll_afp_quote_indicator.dependent_rate_afp = capital_dependent_rate_afp
                payroll_afp_quote_indicator.dependent_sis = capital_dependent_sis
                payroll_afp_quote_indicator.independent_rate_afp = capital_independent_rate_afp
                payroll_afp_quote_indicator.period = payroll_indicator_inputs['period']
                payroll_afp_quote_indicator.added_date = datetime.now()
                self.db.add(payroll_afp_quote_indicator)
                self.db.commit()

            if pention_id == 6:
                modelo_dependent_rate_afp = HelperClass().remove_from_string(".", payroll_indicator_inputs['modelo_dependent_rate_afp'])
                modelo_dependent_rate_afp = HelperClass().replace(",", ".", modelo_dependent_rate_afp)
                modelo_dependent_sis = HelperClass().remove_from_string(".", payroll_indicator_inputs['modelo_dependent_sis'])
                modelo_dependent_sis = HelperClass().replace(",", ".", modelo_dependent_sis)
                modelo_independent_rate_afp = HelperClass().remove_from_string(".", payroll_indicator_inputs['modelo_independent_rate_afp'])
                modelo_independent_rate_afp = HelperClass().replace(",", ".", modelo_independent_rate_afp)

                payroll_afp_quote_indicator = PayrollAfpQuoteIndicatorModel()
                payroll_afp_quote_indicator.pention_id = pention_id
                payroll_afp_quote_indicator.dependent_rate_afp = modelo_dependent_rate_afp
                payroll_afp_quote_indicator.dependent_sis = modelo_dependent_sis
                payroll_afp_quote_indicator.independent_rate_afp = modelo_independent_rate_afp
                payroll_afp_quote_indicator.period = payroll_indicator_inputs['period']
                payroll_afp_quote_indicator.added_date = datetime.now()
                self.db.add(payroll_afp_quote_indicator)
                self.db.commit()

            if pention_id == 7: 
                uno_dependent_rate_afp = HelperClass().remove_from_string(".", payroll_indicator_inputs['uno_dependent_rate_afp'])
                uno_dependent_rate_afp = HelperClass().replace(",", ".", uno_dependent_rate_afp)
                uno_dependent_sis_input = HelperClass().remove_from_string(".", payroll_indicator_inputs['uno_dependent_sis_input'])
                uno_dependent_sis_input = HelperClass().replace(",", ".", uno_dependent_sis_input)
                uno_independent_rate_afp = HelperClass().remove_from_string(".", payroll_indicator_inputs['uno_independent_rate_afp'])
                uno_independent_rate_afp = HelperClass().replace(",", ".", uno_independent_rate_afp)

                payroll_afp_quote_indicator = PayrollAfpQuoteIndicatorModel()
                payroll_afp_quote_indicator.pention_id = pention_id
                payroll_afp_quote_indicator.dependent_rate_afp = uno_dependent_rate_afp
                payroll_afp_quote_indicator.dependent_sis = uno_dependent_sis_input
                payroll_afp_quote_indicator.independent_rate_afp = uno_independent_rate_afp
                payroll_afp_quote_indicator.period = payroll_indicator_inputs['period']
                payroll_afp_quote_indicator.added_date = datetime.now()
                self.db.add(payroll_afp_quote_indicator)
                self.db.commit()

            inserted_id = payroll_afp_quote_indicator.id

            return inserted_id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"