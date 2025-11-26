from app.backend.db.models import PayrollMiniumTaxableIncomeIndicatorModel
from app.backend.classes.helper_class import HelperClass
from datetime import datetime

class PayrollMiniumTaxableIncomeIndicatorClass:
    def __init__(self, db):
        self.db = db

    def get(self, period):
        data = self.db.query(PayrollMiniumTaxableIncomeIndicatorModel).filter(PayrollMiniumTaxableIncomeIndicatorModel.period == period).first()

        return data
    
    def store(self, payroll_indicator_inputs):
        try:
            minimun_income_tax_dependent_independet = HelperClass().remove_from_string(".", payroll_indicator_inputs['minimun_income_tax_dependent_independet'])
            minimun_income_tax_dependent_independet = HelperClass().replace(",", ".", minimun_income_tax_dependent_independet)
            minimun_income_tax_under_18_over_65 = HelperClass().remove_from_string(".", payroll_indicator_inputs['minimun_income_tax_under_18_over_65'])
            minimun_income_tax_under_18_over_65 = HelperClass().replace(",", ".", minimun_income_tax_under_18_over_65)
            minimun_income_tax_domestic_worker = HelperClass().remove_from_string(".", payroll_indicator_inputs['minimun_income_tax_domestic_worker'])
            minimun_income_tax_domestic_worker = HelperClass().replace(",", ".", minimun_income_tax_domestic_worker)
            minimun_income_tax_non_remunerational = HelperClass().remove_from_string(".", payroll_indicator_inputs['minimun_income_tax_non_remunerational'])
            minimun_income_tax_non_remunerational = HelperClass().replace(",", ".", minimun_income_tax_non_remunerational)

            payroll_minium_taxable_income_indicator = PayrollMiniumTaxableIncomeIndicatorModel()
            payroll_minium_taxable_income_indicator.dependent_independent_workers = minimun_income_tax_dependent_independet
            payroll_minium_taxable_income_indicator.under_18_over_65 = minimun_income_tax_under_18_over_65
            payroll_minium_taxable_income_indicator.particular_home = minimun_income_tax_domestic_worker
            payroll_minium_taxable_income_indicator.no_remunerations = minimun_income_tax_non_remunerational
            payroll_minium_taxable_income_indicator.period = payroll_indicator_inputs['period']
            payroll_minium_taxable_income_indicator.added_date = datetime.now()
            self.db.add(payroll_minium_taxable_income_indicator)
            self.db.commit()
            
            inserted_id = payroll_minium_taxable_income_indicator.id

            return inserted_id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"