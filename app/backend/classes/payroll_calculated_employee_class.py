from app.backend.db.models import PayrollCalculatedEmployeeModel

class PayrollCalculatedEmployeeClass:
    def __init__(self, db):
        self.db = db

    def check(self, period):
        data = self.db.query(PayrollCalculatedEmployeeModel).filter(PayrollCalculatedEmployeeModel.period == period).first()

        return data

    def store(self, i, period):
        quantity = self.db.query(PayrollCalculatedEmployeeModel).filter(PayrollCalculatedEmployeeModel.period == period).count()
        
        if quantity > 0:
            payroll_calculated_employee = self.db.query(PayrollCalculatedEmployeeModel).filter(PayrollCalculatedEmployeeModel.period == period).one_or_none()
            payroll_calculated_employee.employee_quantity = i
            self.db.add(payroll_calculated_employee)
        
            try:
                self.db.commit()

                return 1
            except Exception as e:
                return 0
        else:
            payroll_calculated_employee = PayrollCalculatedEmployeeModel()
            payroll_calculated_employee.employee_quantity = i
            payroll_calculated_employee.period = period

            self.db.add(payroll_calculated_employee)

            try:
                self.db.commit()

                return 1
            except Exception as e:
                error_message = str(e)
                return f"Error: {error_message}"