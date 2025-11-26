from app.backend.db.models import PayrollSecondCategoryTaxModel
from app.backend.classes.helper_class import HelperClass
from datetime import datetime

class PayrollSecondCategoryTaxClass:
    def __init__(self, db):
        self.db = db
          
    def get(self, period, taxable_assets):
        data = self.db.query(PayrollSecondCategoryTaxModel).filter(
            PayrollSecondCategoryTaxModel.period == period,
            PayrollSecondCategoryTaxModel.since >= taxable_assets,
            PayrollSecondCategoryTaxModel.until <= taxable_assets
        ).first()

        return data
    

    def store(self, payroll_sencond_category_tax_inputs):
        try:
            since_1 = HelperClass().remove_from_string(".", payroll_sencond_category_tax_inputs['since_1'])
            since_1 = HelperClass().replace(",", ".", since_1)
            since_1 = HelperClass().remove_from_string(" ", since_1)
            until_1 = HelperClass().remove_from_string(".", payroll_sencond_category_tax_inputs['until_1'])
            until_1 = HelperClass().replace(",", ".", until_1)
            until_1 = HelperClass().remove_from_string(" ", until_1)
            factor_1 = HelperClass().remove_from_string(".", payroll_sencond_category_tax_inputs['factor_1'])
            factor_1 = HelperClass().replace(",", ".", factor_1)
            factor_1 = HelperClass().remove_from_string(" ", factor_1)
            discount_1 = HelperClass().remove_from_string(".", payroll_sencond_category_tax_inputs['discount_1'])
            discount_1 = HelperClass().replace(",", ".", discount_1)
            discount_1 = HelperClass().remove_from_string(" ", discount_1)

            since_2 = HelperClass().remove_from_string(".", payroll_sencond_category_tax_inputs['since_2'])
            since_2 = HelperClass().replace(",", ".", since_2)
            since_2 = HelperClass().remove_from_string(" ", since_2)
            until_2 = HelperClass().remove_from_string(".", payroll_sencond_category_tax_inputs['until_2'])
            until_2 = HelperClass().replace(",", ".", until_2)
            until_2 = HelperClass().remove_from_string(" ", until_2)
            factor_2 = HelperClass().remove_from_string(".", payroll_sencond_category_tax_inputs['factor_2'])
            factor_2 = HelperClass().replace(",", ".", factor_2)
            factor_2 = HelperClass().remove_from_string(" ", factor_2)
            discount_2 = HelperClass().remove_from_string(".", payroll_sencond_category_tax_inputs['discount_2'])
            discount_2 = HelperClass().replace(",", ".", discount_2)
            discount_2 = HelperClass().remove_from_string(" ", discount_2)

            since_3 = HelperClass().remove_from_string(".", payroll_sencond_category_tax_inputs['since_3'])
            since_3 = HelperClass().replace(",", ".", since_3)
            since_3 = HelperClass().remove_from_string(" ", since_3)
            until_3 = HelperClass().remove_from_string(".", payroll_sencond_category_tax_inputs['until_3'])
            until_3 = HelperClass().replace(",", ".", until_3)
            until_3 = HelperClass().remove_from_string(" ", until_3)
            factor_3 = HelperClass().remove_from_string(".", payroll_sencond_category_tax_inputs['factor_3'])
            factor_3 = HelperClass().replace(",", ".", factor_3)
            factor_3 = HelperClass().remove_from_string(" ", factor_3)
            discount_3 = HelperClass().remove_from_string(".", payroll_sencond_category_tax_inputs['discount_3'])
            discount_3 = HelperClass().replace(",", ".", discount_3)
            discount_3 = HelperClass().remove_from_string(" ", discount_3)

            since_4 = HelperClass().remove_from_string(".", payroll_sencond_category_tax_inputs['since_4'])
            since_4 = HelperClass().replace(",", ".", since_4)
            since_4 = HelperClass().remove_from_string(" ", since_4)
            until_4 = HelperClass().remove_from_string(".", payroll_sencond_category_tax_inputs['until_4'])
            until_4 = HelperClass().replace(",", ".", until_4)
            until_4 = HelperClass().remove_from_string(" ", until_4)
            factor_4 = HelperClass().remove_from_string(".", payroll_sencond_category_tax_inputs['factor_4'])
            factor_4 = HelperClass().replace(",", ".", factor_4)
            factor_4 = HelperClass().remove_from_string(" ", factor_4)
            discount_4 = HelperClass().remove_from_string(".", payroll_sencond_category_tax_inputs['discount_4'])
            discount_4 = HelperClass().replace(",", ".", discount_4)
            discount_4 = HelperClass().remove_from_string(" ", discount_4)

            payroll_second_category_tax = PayrollSecondCategoryTaxModel()
            payroll_second_category_tax.period = payroll_sencond_category_tax_inputs['period']
            payroll_second_category_tax.since = since_1
            payroll_second_category_tax.until = until_1
            payroll_second_category_tax.factor = factor_1
            payroll_second_category_tax.discount = discount_1
            payroll_second_category_tax.added_date = datetime.now()
            payroll_second_category_tax.updated_date = datetime.now()
            self.db.add(payroll_second_category_tax)
            self.db.commit()

            payroll_second_category_tax = PayrollSecondCategoryTaxModel()
            payroll_second_category_tax.period = payroll_sencond_category_tax_inputs['period']
            payroll_second_category_tax.since = since_2
            payroll_second_category_tax.until = until_2
            payroll_second_category_tax.factor = factor_2
            payroll_second_category_tax.discount = discount_2
            payroll_second_category_tax.added_date = datetime.now()
            payroll_second_category_tax.updated_date = datetime.now()
            self.db.add(payroll_second_category_tax)
            self.db.commit()

            payroll_second_category_tax = PayrollSecondCategoryTaxModel()
            payroll_second_category_tax.period = payroll_sencond_category_tax_inputs['period']
            payroll_second_category_tax.since = since_3
            payroll_second_category_tax.until = until_3
            payroll_second_category_tax.factor = factor_3
            payroll_second_category_tax.discount = discount_3
            payroll_second_category_tax.added_date = datetime.now()
            payroll_second_category_tax.updated_date = datetime.now()
            self.db.add(payroll_second_category_tax)
            self.db.commit()

            payroll_second_category_tax = PayrollSecondCategoryTaxModel()
            payroll_second_category_tax.period = payroll_sencond_category_tax_inputs['period']
            payroll_second_category_tax.since = since_4
            payroll_second_category_tax.until = until_4
            payroll_second_category_tax.factor = factor_4
            payroll_second_category_tax.discount = discount_4
            payroll_second_category_tax.added_date = datetime.now()
            payroll_second_category_tax.updated_date = datetime.now()
            self.db.add(payroll_second_category_tax)
            self.db.commit()
            
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"