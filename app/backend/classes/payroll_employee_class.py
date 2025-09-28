from app.backend.db.models import PayrollEmployeeModel
import json
from datetime import datetime

class PayrollEmployeeClass:
    def __init__(self, db):
        self.db = db

    def get(self, rut, period = None):
        try:
            data = self.db.query(PayrollEmployeeModel).filter(PayrollEmployeeModel.rut == rut).filter(PayrollEmployeeModel.period == period).all()
                
            if not data:
                return "No data found"
            serialized_data = []
            for payroll_employee in data:
                serialized_data.append({
                    "id": payroll_employee.id,
                    "rut": payroll_employee.rut,
                    "visual_rut": payroll_employee.visual_rut,
                    "period": payroll_employee.period,
                    "contract_type_id": payroll_employee.contract_type_id,
                    "branch_office_id": payroll_employee.branch_office_id,
                    "health_id": payroll_employee.health_id,
                    "pention_id": payroll_employee.pention_id,
                    "employee_type_id": payroll_employee.employee_type_id,
                    "regime_id": payroll_employee.regime_id,
                    "health_payment_id": payroll_employee.health_payment_id,
                    "extra_health_payment_type_id": payroll_employee.extra_health_payment_type_id,
                    "apv_payment_type_id": payroll_employee.apv_payment_type_id,
                    "salary": payroll_employee.salary,
                    "collation": payroll_employee.collation,
                    "locomotion": payroll_employee.locomotion,
                    "extra_health_amount": payroll_employee.extra_health_amount,
                    "apv_amount": payroll_employee.apv_amount,
                    "names": payroll_employee.names,
                    "father_lastname": payroll_employee.father_lastname,
                    "mother_lastname": payroll_employee.mother_lastname,
                    "added_date": payroll_employee.added_date,
                    "updated_date": payroll_employee.updated_date
                })
            return serialized_data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get_all(self, period = None, page=0, items_per_page=10):
        try:
            if period == None:
                data = self.db.query(PayrollEmployeeModel).order_by('rut').all()
            else:
                data = self.db.query(PayrollEmployeeModel).filter(PayrollEmployeeModel.period == period).order_by('rut').all()
                
            if not data:
                return "No data found"
            serialized_data = []
            for payroll_employee in data:
                serialized_data.append({
                    "id": payroll_employee.id,
                    "rut": payroll_employee.rut,
                    "visual_rut": payroll_employee.visual_rut,
                    "period": payroll_employee.period,
                    "contract_type_id": payroll_employee.contract_type_id,
                    "branch_office_id": payroll_employee.branch_office_id,
                    "health_id": payroll_employee.health_id,
                    "pention_id": payroll_employee.pention_id,
                    "employee_type_id": payroll_employee.employee_type_id,
                    "regime_id": payroll_employee.regime_id,
                    "health_payment_id": payroll_employee.health_payment_id,
                    "extra_health_payment_type_id": payroll_employee.extra_health_payment_type_id,
                    "apv_payment_type_id": payroll_employee.apv_payment_type_id,
                    "salary": payroll_employee.salary,
                    "collation": payroll_employee.collation,
                    "locomotion": payroll_employee.locomotion,
                    "extra_health_amount": payroll_employee.extra_health_amount,
                    "apv_amount": payroll_employee.apv_amount,
                    "names": payroll_employee.names,
                    "father_lastname": payroll_employee.father_lastname,
                    "mother_lastname": payroll_employee.mother_lastname,
                    "added_date": payroll_employee.added_date,
                    "updated_date": payroll_employee.updated_date
                })
            return serialized_data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def search(self, search_inputs):
        try:
            if len(search_inputs) > 0:
                search_rut = search_inputs['rut']
                search_father_lastname = search_inputs['father_lastname']

            data_query = self.db.query(PayrollEmployeeModel).order_by('rut')

            if len(search_inputs) > 0:
                if search_rut:
                    data_query = data_query.filter(PayrollEmployeeModel.visual_rut.like(f"%{search_rut}%"))
                if search_father_lastname:
                    data_query = data_query.filter(PayrollEmployeeModel.father_lastname.like(f"%{search_father_lastname}%"))

            data = data_query.all()

            if not data:
                return "No data found"
            
            serialized_data = []
            for payroll_employee in data:
                serialized_data.append({
                    "id": payroll_employee.id,
                    "rut": payroll_employee.rut,
                    "visual_rut": payroll_employee.visual_rut,
                    "period": payroll_employee.period,
                    "contract_type_id": payroll_employee.contract_type_id,
                    "branch_office_id": payroll_employee.branch_office_id,
                    "health_id": payroll_employee.health_id,
                    "pention_id": payroll_employee.pention_id,
                    "employee_type_id": payroll_employee.employee_type_id,
                    "regime_id": payroll_employee.regime_id,
                    "health_payment_id": payroll_employee.health_payment_id,
                    "extra_health_payment_type_id": payroll_employee.extra_health_payment_type_id,
                    "apv_payment_type_id": payroll_employee.apv_payment_type_id,
                    "salary": payroll_employee.salary,
                    "collation": payroll_employee.collation,
                    "locomotion": payroll_employee.locomotion,
                    "extra_health_amount": payroll_employee.extra_health_amount,
                    "apv_amount": payroll_employee.apv_amount,
                    "names": payroll_employee.names,
                    "father_lastname": payroll_employee.father_lastname,
                    "mother_lastname": payroll_employee.mother_lastname,
                    "added_date": payroll_employee.added_date,
                    "updated_date": payroll_employee.updated_date
                })
            
            return serialized_data
        
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        