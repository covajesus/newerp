from app.backend.classes.payroll_employee_class import PayrollEmployeeClass
from app.backend.classes.payroll_item_value_class import PayrollItemValueClass
from app.backend.classes.payroll_taxable_income_cap_indicator_class import PayrollTaxableIncomeCapIndicatorClass
from app.backend.classes.payroll_item_class import PayrollItemClass
from app.backend.classes.payroll_uf_indicator_class import PayrollUfIndicatorClass
from app.backend.classes.payroll_minium_taxable_income_indicator_class import PayrollMiniumTaxableIncomeIndicatorClass
from app.backend.classes.payroll_afp_quote_indicator_class import PayrollAfpQuoteIndicatorClass
from app.backend.classes.payroll_umployment_insurance_indicator_class import PayrollUmploymentInsuranceIndicatorClass
from app.backend.classes.payroll_second_category_tax_class import PayrollSecondCategoryTaxClass
from app.backend.classes.payroll_ccaf_indicator_class import PayrollCcafIndicatorClass
from app.backend.classes.medical_license_class import MedicalLicenseClass
from app.backend.classes.payroll_other_indicator_class import PayrollOtherIndicatorClass
from app.backend.classes.payroll_calculated_employee_class import PayrollCalculatedEmployeeClass
from app.backend.classes.salary_settlement_class import SalarySettlementClass

class PayrollCalculationClass:
    def __init__(self, db):
        self.db = db

    def calculate(self, rut, period=None, batch_size=20):
        employee = PayrollEmployeeClass(self.db).get(rut, period)
        self.process_employee(employee, period)

        return 1

    def process_employee(self, employee, period):
        self.proportional(employee[0]['rut'], 35, period, 0, 1)
        self.proportional(employee[0]['rut'], 36, period, 0, 1)
        self.proportional(employee[0]['rut'], 37, period, 0, 1)
        self.taxable_salary(employee[0]['rut'], period)
        self.no_taxable_salary(employee[0]['rut'], period)
        self.gratification(employee[0]['rut'], period)
        self.taxable_assets(employee[0]['rut'], period)
        self.no_taxable_assets(employee[0]['rut'], period)
        self.health(employee[0]['rut'], period, employee[0]['extra_health_payment_type_id'], employee[0]['extra_health_amount'])
        self.pention(employee[0]['rut'], period, employee[0]['pention_id'], employee[0]['regime_id'])
        self.worker_unemployment_insurance(employee[0]['rut'], period, employee[0]['regime_id'], employee[0]['contract_type_id'])
        self.employer_unemployment_insurance(employee[0]['rut'], period, employee[0]['regime_id'], employee[0]['contract_type_id'])
        # self.ccaf_calculated_quote(employee[0]['rut'], period, employee[0]['health_payment_id'])
        self.second_level_insurance(employee[0]['rut'], period)
        self.legal_discount(employee[0]['rut'], period)
        self.other_discount(employee[0]['rut'], period)
        self.total_assets(employee[0]['rut'], period)
        self.total_discounts(employee[0]['rut'], period)
        self.disability_survival_insurance(employee[0]['rut'], period, employee[0]['pention_id'])
        self.total_to_pay(employee[0]['rut'], period)
    
    def taxable_salary(self, rut, period):
        taxable_items = PayrollItemClass(self.db).get_taxable_items()
        taxable_total = 0

        for taxable_item in taxable_items:
            payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, taxable_item.id, period)
            
            if payroll_item_value is not None:
                if taxable_item.classification_id == 1:
                    taxable_total += payroll_item_value.amount
                elif  taxable_item.classification_id == 2:
                    taxable_total -= payroll_item_value.amount
    
        payroll_item_value_data = {}
        payroll_item_value_data['item_id'] = 38
        payroll_item_value_data['rut'] = rut
        payroll_item_value_data['period'] = period
        payroll_item_value_data['amount'] = taxable_total

        PayrollItemValueClass(self.db).store(payroll_item_value_data)

        return taxable_total

    def proportional(self, rut, item_id, period, amount = 0, manual_status_id = 0):
        if manual_status_id == 1:
            payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, item_id, period)
            days = PayrollItemValueClass(self.db).get_with_period(rut, 55, period)

            if payroll_item_value != None and days != None:
                total = (payroll_item_value.amount / 30) * days.amount
            else:
                total = 0

            if item_id == 35:
                item_id = 52
            elif item_id == 36:
                item_id = 53
            elif item_id == 37:
                item_id = 54

            payroll_item_value_data = {}
            payroll_item_value_data['item_id'] = item_id
            payroll_item_value_data['rut'] = rut
            payroll_item_value_data['period'] = period
            payroll_item_value_data['amount'] = total

            PayrollItemValueClass(self.db).store(payroll_item_value_data)
        else:
            days = PayrollItemValueClass(self.db).get_with_period(rut, 55, period)
    
            total = (float(amount) / 30) * days.amount

            return total
    
    def no_taxable_salary(self, rut, period):
        no_taxable_items = PayrollItemClass(self.db).get_no_taxable_items()

        no_taxable_total = 0

        for no_taxable_item in no_taxable_items:
            payroll_item_value = PayrollItemValueClass(self.db).get(rut, no_taxable_item.id)

            if payroll_item_value is not None:
                no_taxable_total += payroll_item_value.amount

        payroll_item_value_data = {}
        payroll_item_value_data['item_id'] = 40
        payroll_item_value_data['rut'] = rut
        payroll_item_value_data['period'] = period
        payroll_item_value_data['amount'] = no_taxable_total

        PayrollItemValueClass(self.db).store(payroll_item_value_data)

        return no_taxable_total
    
    def gratification(self, rut, period):
        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 38, period)
        imponible_salary = payroll_item_value.amount
        payroll_minium_taxable_income_indicator = PayrollMiniumTaxableIncomeIndicatorClass(self.db).get(period)
        top_minimal_salary = payroll_minium_taxable_income_indicator.dependent_independent_workers
        payroll_other_indicator = PayrollOtherIndicatorClass(self.db).get(period, 1)
        cap_value = (top_minimal_salary * 4.75)/12

        if (imponible_salary * 0.25) > cap_value:
            amount = cap_value
        else:
            amount = imponible_salary * 0.25

        payroll_item_value_data = {}
        payroll_item_value_data['item_id'] = 39
        payroll_item_value_data['rut'] = rut
        payroll_item_value_data['period'] = period
        payroll_item_value_data['amount'] = amount

        PayrollItemValueClass(self.db).store(payroll_item_value_data)

        return amount
    
    def taxable_assets(self, rut, period):
        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 38, period)
        taxable_salary = payroll_item_value.amount

        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 39, period)
        gratification = payroll_item_value.amount

        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 13, period)
        if payroll_item_value is not None:
            absenteeism = payroll_item_value.amount
        else:
            absenteeism = 0

        amount = taxable_salary + gratification - absenteeism

        payroll_item_value_data = {}
        payroll_item_value_data['item_id'] = 57
        payroll_item_value_data['rut'] = rut
        payroll_item_value_data['period'] = period
        payroll_item_value_data['amount'] = amount

        PayrollItemValueClass(self.db).store(payroll_item_value_data)

        return amount

    def no_taxable_assets(self, rut, period):
        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 40, period)
        no_taxable_salary = payroll_item_value.amount

        amount = no_taxable_salary

        payroll_item_value_data = {}
        payroll_item_value_data['item_id'] = 58
        payroll_item_value_data['rut'] = rut
        payroll_item_value_data['period'] = period
        payroll_item_value_data['amount'] = amount

        PayrollItemValueClass(self.db).store(payroll_item_value_data)

    def health(self, rut, period, extra_health_payment_type_id, extra_health_amount):
        payroll_taxable_income_cap_indicator = PayrollTaxableIncomeCapIndicatorClass(self.db).get(period)
        payroll_uf_indicator = PayrollUfIndicatorClass(self.db).get(period)

        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 57, period)
        taxable_assets = payroll_item_value.amount

        if extra_health_payment_type_id > 0:
  
            if extra_health_payment_type_id == 1:
                if taxable_assets > payroll_taxable_income_cap_indicator.afp:
                    calculation = payroll_taxable_income_cap_indicator.afp * 0.07
                else:
                    calculation = taxable_assets * 0.07

                health_amount = extra_health_amount
                
                if health_amount < calculation:
                    health_amount = calculation

                    aditional_health_amount = 0
                else:
                    aditional_health_amount = health_amount - calculation
            else:
                if taxable_assets > payroll_taxable_income_cap_indicator.afp:
                    calculation = payroll_taxable_income_cap_indicator.afp * 0.07
                else:
                    calculation = taxable_assets * 0.07

                health_amount = float(extra_health_amount) * payroll_uf_indicator.uf_value_current_month
                
                if health_amount < calculation:
                    health_amount = calculation

                    aditional_health_amount = 0
                else:
                    aditional_health_amount = health_amount - calculation


            health_amount = health_amount - aditional_health_amount

            payroll_item_value_data = {}
            payroll_item_value_data['item_id'] = 41
            payroll_item_value_data['rut'] = rut
            payroll_item_value_data['period'] = period
            payroll_item_value_data['amount'] = health_amount

            PayrollItemValueClass(self.db).store(payroll_item_value_data)

            payroll_item_value_data = {}
            payroll_item_value_data['item_id'] = 29
            payroll_item_value_data['rut'] = rut
            payroll_item_value_data['period'] = period
            payroll_item_value_data['amount'] = aditional_health_amount

            PayrollItemValueClass(self.db).store(payroll_item_value_data)
        else:
            if taxable_assets > payroll_taxable_income_cap_indicator.afp:
                amount = payroll_taxable_income_cap_indicator.afp * 0.07
            else:
                amount = taxable_assets * 0.07

            payroll_item_value_data = {}
            payroll_item_value_data['item_id'] = 41
            payroll_item_value_data['rut'] = rut
            payroll_item_value_data['period'] = period
            payroll_item_value_data['amount'] = amount

            PayrollItemValueClass(self.db).store(payroll_item_value_data)

    def ccaf_calculated_quote(self, rut, period, health_type_id):
        payroll_ccaf_indicator = PayrollCcafIndicatorClass(self.db).get(period)

        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 57, period)
        taxable_assets = payroll_item_value.amount

        if health_type_id == 2:
            amount = round((taxable_assets * payroll_ccaf_indicator.ccaf)/100)

        payroll_item_value_data = {}
        payroll_item_value_data['item_id'] = 73
        payroll_item_value_data['rut'] = rut
        payroll_item_value_data['period'] = period
        payroll_item_value_data['amount'] = amount

        PayrollItemValueClass(self.db).store(payroll_item_value_data)

    def mutuality_quote(self, rut, period):
        payroll_other_indicator = PayrollOtherIndicatorClass(self.db).get(period, 1)

        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 57, period)
        taxable_assets = payroll_item_value.amount

        amount = round((taxable_assets * payroll_other_indicator.mutual_value)/100)

        payroll_item_value_data = {}
        payroll_item_value_data['item_id'] = 73
        payroll_item_value_data['rut'] = rut
        payroll_item_value_data['period'] = period
        payroll_item_value_data['amount'] = amount
        
    def pention(self, rut, period, pention_id, regime_id):
        if regime_id == 1:
            payroll_taxable_income_cap_indicator = PayrollTaxableIncomeCapIndicatorClass(self.db).get(period)
            payroll_afp_quote = PayrollAfpQuoteIndicatorClass(self.db).get(pention_id, period)

            payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 57, period)
            taxable_assets = payroll_item_value.amount

            if taxable_assets > payroll_taxable_income_cap_indicator.afp:
                pention_amount = (payroll_taxable_income_cap_indicator.afp * payroll_afp_quote.dependent_rate_afp)/100
            else:
                pention_amount = (taxable_assets * payroll_afp_quote.dependent_rate_afp)/100

            amount = self.proportional(rut, 0, period, pention_amount, 0)
        else:
            amount = 0

        payroll_item_value_data = {}
        payroll_item_value_data['item_id'] = 59
        payroll_item_value_data['rut'] = rut
        payroll_item_value_data['period'] = period
        payroll_item_value_data['amount'] = amount

        PayrollItemValueClass(self.db).store(payroll_item_value_data)

    def employer_unemployment_insurance(self, rut, period, regime_id, contract_type_id):
        payroll_taxable_income_cap_indicator = PayrollTaxableIncomeCapIndicatorClass(self.db).get(period)

        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 57, period)
        taxable_assets = payroll_item_value.amount

        if regime_id == 2 or regime_id == 3:
            amount = 0
        else:
            payroll_item_value_days = PayrollItemValueClass(self.db).get_with_period(rut, 55, period)

            payroll_umployment_insurance_indicator = PayrollUmploymentInsuranceIndicatorClass(self.db).get(contract_type_id, period)

            if payroll_item_value_days.amount > 0:
                if taxable_assets > payroll_taxable_income_cap_indicator.unemployment:
                    taxable_assets = payroll_taxable_income_cap_indicator.unemployment

                if contract_type_id == 1:
                    amount = (payroll_umployment_insurance_indicator.employer/100) * taxable_assets
                elif contract_type_id == 2:
                    amount = (payroll_umployment_insurance_indicator.employer/100) * taxable_assets
                else:
                    amount = (payroll_umployment_insurance_indicator.employer/100) * taxable_assets
            else:
                payroll_item_value_taxable_assets = PayrollItemValueClass(self.db).get_with_period(rut, 57, period)

                if taxable_assets > payroll_taxable_income_cap_indicator.unemployment:
                    taxable_assets = payroll_taxable_income_cap_indicator.unemployment
                else:
                    taxable_assets = payroll_item_value_taxable_assets.amount

                if contract_type_id == 1:
                    amount = (payroll_umployment_insurance_indicator.employer/100) * taxable_assets
                elif contract_type_id == 2:
                    amount = (payroll_umployment_insurance_indicator.employer/100) * taxable_assets
                else:
                    amount = (payroll_umployment_insurance_indicator.employer/100) * taxable_assets

        payroll_item_value_data = {}
        payroll_item_value_data['item_id'] = 61
        payroll_item_value_data['rut'] = rut
        payroll_item_value_data['period'] = period
        payroll_item_value_data['amount'] = amount

        PayrollItemValueClass(self.db).store(payroll_item_value_data)

    def worker_unemployment_insurance(self, rut, period, regime_id, contract_type_id):
        payroll_taxable_income_cap_indicator = PayrollTaxableIncomeCapIndicatorClass(self.db).get(period)

        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 57, period)
        taxable_assets = payroll_item_value.amount

        if regime_id == 2 or regime_id == 3:
            amount = 0
        else:
            payroll_item_value_days = PayrollItemValueClass(self.db).get_with_period(rut, 55, period)

            payroll_umployment_insurance_indicator = PayrollUmploymentInsuranceIndicatorClass(self.db).get(contract_type_id, period)

            if taxable_assets > payroll_taxable_income_cap_indicator.unemployment:
                    taxable_assets = payroll_taxable_income_cap_indicator.unemployment

            if payroll_item_value_days.amount > 0:
                
                if contract_type_id == 1:
                    amount = (payroll_umployment_insurance_indicator.worker/100) * taxable_assets
                elif contract_type_id == 2:
                    amount = (payroll_umployment_insurance_indicator.worker/100) * taxable_assets
                else:
                    amount = (payroll_umployment_insurance_indicator.worker/100) * taxable_assets
            else:
                if contract_type_id == 1:
                    amount = (payroll_umployment_insurance_indicator.employer/100) * taxable_assets
                elif contract_type_id == 2:
                    amount = (payroll_umployment_insurance_indicator.employer/100) * taxable_assets
                else:
                    amount = (payroll_umployment_insurance_indicator.employer/100) * taxable_assets

        payroll_item_value_data = {}
        payroll_item_value_data['item_id'] = 30
        payroll_item_value_data['rut'] = rut
        payroll_item_value_data['period'] = period
        payroll_item_value_data['amount'] = amount

        PayrollItemValueClass(self.db).store(payroll_item_value_data)

    def legal_discount(self, rut, period):
        legal_discount_items = PayrollItemClass(self.db).get_legal_discount_items()

        legal_discount_total = 0

        for legal_discount_item in legal_discount_items:
            legal_discount_item_value = PayrollItemValueClass(self.db).get_with_period(rut, legal_discount_item.id, period)
            
            if legal_discount_item_value is not None:
                legal_discount_total += legal_discount_item_value.amount
            else:
                legal_discount_total += 0

        payroll_item_value_data = {}
        payroll_item_value_data['item_id'] = 63
        payroll_item_value_data['rut'] = rut
        payroll_item_value_data['period'] = period
        payroll_item_value_data['amount'] = legal_discount_total

        PayrollItemValueClass(self.db).store(payroll_item_value_data)

    def other_discount(self, rut, period):
        other_discount_items = PayrollItemClass(self.db).get_other_discout_items()

        other_discount_total = 0

        for other_discount_item in other_discount_items:
            other_discount_item_value = PayrollItemValueClass(self.db).get_with_period(rut, other_discount_item.id, period)

            if other_discount_item_value is not None:
                other_discount_total += other_discount_item_value.amount

        payroll_item_value_data = {}
        payroll_item_value_data['item_id'] = 23
        payroll_item_value_data['rut'] = rut
        payroll_item_value_data['period'] = period
        payroll_item_value_data['amount'] = other_discount_total

        PayrollItemValueClass(self.db).store(payroll_item_value_data)

    def second_level_insurance(self, rut, period):
        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 57, period)
        taxable_assets = payroll_item_value.amount

        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 59, period)
        if payroll_item_value is not None:
            pention = payroll_item_value.amount
        else:
            pention = 0

        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 41, period)
        if payroll_item_value is not None:
            health = payroll_item_value.amount
        else:
            health = 0

        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 30, period)
        if payroll_item_value is not None:
            unemployment_insurance = payroll_item_value.amount
        else:
            unemployment_insurance = 0

        total = taxable_assets - pention - health - unemployment_insurance

        payroll_second_category_tax_indicator = PayrollSecondCategoryTaxClass(self.db).get(period, total)
        discount = payroll_second_category_tax_indicator.discount
        factor = payroll_second_category_tax_indicator.factor
        
        if factor != 0:
            amount = round((total * float(factor)) - float(discount))

            payroll_item_value_data = {}
            payroll_item_value_data['item_id'] = 102
            payroll_item_value_data['rut'] = rut
            payroll_item_value_data['period'] = period
            payroll_item_value_data['amount'] = total

            PayrollItemValueClass(self.db).store(payroll_item_value_data)

            payroll_item_value_data = {}
            payroll_item_value_data['item_id'] = 103
            payroll_item_value_data['rut'] = rut
            payroll_item_value_data['period'] = period
            payroll_item_value_data['amount'] = factor

            PayrollItemValueClass(self.db).store(payroll_item_value_data)
            
            payroll_item_value_data = {}
            payroll_item_value_data['item_id'] = 104
            payroll_item_value_data['rut'] = rut
            payroll_item_value_data['period'] = period
            payroll_item_value_data['amount'] = discount

            PayrollItemValueClass(self.db).store(payroll_item_value_data)
        else:
            amount = 0

        payroll_item_value_data = {}
        payroll_item_value_data['item_id'] = 65
        payroll_item_value_data['rut'] = rut
        payroll_item_value_data['period'] = period
        payroll_item_value_data['amount'] = amount

        PayrollItemValueClass(self.db).store(payroll_item_value_data)

    def total_assets(self, rut, period):
        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 57, period)
        taxable_assets = payroll_item_value.amount

        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 58, period)
        no_taxable_assets = payroll_item_value.amount

        amount = taxable_assets + no_taxable_assets

        payroll_item_value_data = {}
        payroll_item_value_data['item_id'] = 66
        payroll_item_value_data['rut'] = rut
        payroll_item_value_data['period'] = period
        payroll_item_value_data['amount'] = amount

        PayrollItemValueClass(self.db).store(payroll_item_value_data)

    def disability_survival_insurance(self, rut, period, pention_id):
        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 57, period)
        taxable_assets = payroll_item_value.amount

        payroll_afp_quote = PayrollAfpQuoteIndicatorClass(self.db).get(pention_id, period)
        amount = (taxable_assets * float(1.49))/100

        payroll_item_value_data = {}
        payroll_item_value_data['item_id'] = 70
        payroll_item_value_data['rut'] = rut
        payroll_item_value_data['period'] = period
        payroll_item_value_data['amount'] = amount

        PayrollItemValueClass(self.db).store(payroll_item_value_data)

    def total_discounts(self, rut, period):
        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 63, period)
        legal_discounts = payroll_item_value.amount

        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 23, period)
        other_discounts = payroll_item_value.amount

        amount = legal_discounts + other_discounts

        payroll_item_value_data = {}
        payroll_item_value_data['item_id'] = 67
        payroll_item_value_data['rut'] = rut
        payroll_item_value_data['period'] = period
        payroll_item_value_data['amount'] = amount

        PayrollItemValueClass(self.db).store(payroll_item_value_data)

    def total_to_pay(self, rut, period):
        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 66, period)
        total_assets = payroll_item_value.amount

        payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, 67, period)
        total_discounts = payroll_item_value.amount

        amount = total_assets - total_discounts

        payroll_item_value_data = {}
        payroll_item_value_data['item_id'] = 68
        payroll_item_value_data['rut'] = rut
        payroll_item_value_data['period'] = period
        payroll_item_value_data['amount'] = amount

        PayrollItemValueClass(self.db).store(payroll_item_value_data)