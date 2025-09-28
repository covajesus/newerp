from app.backend.db.models import PayrollItemValueModel, PayrollItemModel
from app.backend.classes.helper_class import HelperClass
from datetime import datetime

class PayrollItemValueClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, item_id = None, period = None):
        data = self.db.query(PayrollItemValueModel).filter(PayrollItemValueModel.item_id == item_id, PayrollItemValueModel.period == period).all()

        return data

    def get_with_period(self, rut, item_id, period):
        data = self.db.query(PayrollItemValueModel).filter(PayrollItemValueModel.rut == rut, PayrollItemValueModel.item_id == item_id, PayrollItemValueModel.period == period).first()

        return data
    
    def get_with_rut_period(self, rut, period):
        data = self.db.query(PayrollItemValueModel).join(PayrollItemModel, PayrollItemModel.id == PayrollItemValueModel.item_id).add_columns(
                PayrollItemValueModel.id,
                PayrollItemValueModel.item_id,
                PayrollItemValueModel.rut,
                PayrollItemValueModel.amount,
                PayrollItemValueModel.period,
                PayrollItemModel.item,
                PayrollItemModel.salary_settlement_name,
                PayrollItemModel.disabled_id
            ).filter(PayrollItemValueModel.rut == rut, PayrollItemValueModel.period == period).all()


        result = []
        for item_value in data:
            result.append({
                "id": item_value.id,
                "item_id": item_value.item_id,
                "rut": item_value.rut,
                "amount": item_value.amount,
                "period": item_value.period,
                "name": item_value.salary_settlement_name,
                "disabled_id": item_value.disabled_id,
                "item": item_value.item
            })

        return result
          
    def get(self, rut, item_id):
        data = self.db.query(PayrollItemValueModel).filter(PayrollItemValueModel.rut == rut, PayrollItemValueModel.item_id == item_id).first()

        return data
    
    def existence(self, rut, item_id, period):
        quantity = self.db.query(PayrollItemValueModel).filter(PayrollItemValueModel.rut == rut, PayrollItemValueModel.item_id == item_id, PayrollItemValueModel.period == period).count()

        return quantity
    
    def delete(self, rut, taxable_id):
        data = self.db.query(PayrollItemValueModel).filter(PayrollItemValueModel.rut == rut, PayrollItemValueModel.item_id == taxable_id).first()

        return data
    
    def delete_with_period(self, rut, item_id, period):
        data = self.db.query(PayrollItemValueModel).filter(PayrollItemValueModel.rut == rut, PayrollItemValueModel.item_id == item_id, PayrollItemValueModel.period == period).first()

        if data != None:
            self.db.delete(data)
            self.db.commit()
            return 1
    
    def store(self, data):
        existence_status = self.existence(data['rut'], data['item_id'], data['period'])

        if existence_status == 0 or existence_status == None:
            amount = float(data['amount'])

            if amount < 0:
                payroll_item_value = PayrollItemValueModel()
                payroll_item_value.rut = data['rut']
                payroll_item_value.item_id = data['item_id']
                payroll_item_value.period = data['period']
                payroll_item_value.amount = 0
                payroll_item_value.added_date = datetime.now()
                payroll_item_value.updated_date = datetime.now()
                self.db.add(payroll_item_value)
                self.db.commit()
            else:
                payroll_item_value = PayrollItemValueModel()
                payroll_item_value.rut = data['rut']
                payroll_item_value.item_id = data['item_id']
                payroll_item_value.period = data['period']
                payroll_item_value.amount = data['amount']
                payroll_item_value.added_date = datetime.now()
                payroll_item_value.updated_date = datetime.now()
                self.db.add(payroll_item_value)
                self.db.commit()
        else:
            self.update(data)


    def update(self, data):
        payroll_item_value = self.db.query(PayrollItemValueModel).filter(PayrollItemValueModel.rut == data['rut'], PayrollItemValueModel.item_id == data['item_id'], PayrollItemValueModel.period == data['period']).first()
        if payroll_item_value:
            payroll_item_value.amount = data['amount']
            payroll_item_value.updated_date = datetime.now()
            self.db.add(payroll_item_value)
            self.db.commit()
            return 1
        else:
            return "No data found"
        
    def update_bulk(self, payroll_item_values):
        for payroll_item_value in payroll_item_values.payroll_item_values:
            rut = payroll_item_value.rut
            item_id = payroll_item_value.item_id
            amount = payroll_item_value.amount
            period = payroll_item_value.period

            payroll_item_value_data = {}
            payroll_item_value_data['item_id'] = item_id
            payroll_item_value_data['rut'] = rut
            payroll_item_value_data['period'] = period
            payroll_item_value_data['amount'] = amount

            existence_status = PayrollItemValueClass(self.db).existence(rut, item_id, period)

            if existence_status > 0 and existence_status != None:
                payroll_item_value = PayrollItemValueClass(self.db).get_with_period(rut, item_id, period)

                if payroll_item_value.amount != amount:
                    if amount == 0 or amount == None:
                        PayrollItemValueClass(self.db).delete_with_period(rut, item_id, period)
                    else:
                        PayrollItemValueClass(self.db).update(payroll_item_value_data)
            else:
                if amount != 0 and amount != None and amount != '0' and amount != '':
                    PayrollItemValueClass(self.db).store(payroll_item_value_data)

        return 1