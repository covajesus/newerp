from app.backend.db.models import PayrollSecondCategoryTaxModel
from datetime import datetime

class PayrollSecondCategoryTaxClass:
    def __init__(self, db):
        self.db = db
          
    def get(self, period, taxable_assets):
        data = self.db.query(PayrollSecondCategoryTaxModel).filter(
            PayrollSecondCategoryTaxModel.period == period,
            PayrollSecondCategoryTaxModel.since <= taxable_assets,
            PayrollSecondCategoryTaxModel.until >= taxable_assets
        ).first()

        return data

    def store(self, payroll_indicator_inputs):
        try:
            payroll_taxable_income_cap_indicator = PayrollTaxableIncomeCapIndicatorModel()
            payroll_taxable_income_cap_indicator.afp = cap_income_tax_afp
            payroll_taxable_income_cap_indicator.ips = cap_income_tax_ips
            payroll_taxable_income_cap_indicator.unemployment = cap_income_tax_unemployment
            payroll_taxable_income_cap_indicator.added_date = datetime.now()
            payroll_taxable_income_cap_indicator.updated_date = datetime.now()
            self.db.add(payroll_taxable_income_cap_indicator)
            self.db.commit()
            
            inserted_id = payroll_taxable_income_cap_indicator.id

            return inserted_id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"