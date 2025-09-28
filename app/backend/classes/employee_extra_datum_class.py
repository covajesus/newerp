from app.backend.db.models import EmployeeExtraModel
from datetime import datetime

class EmployeeExtraDatumClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(EmployeeExtraModel).order_by(EmployeeExtraModel.id).all()
            if not data:
                return "No hay registros"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(EmployeeExtraModel).filter(EmployeeExtraModel.rut == value).first()
       
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, employee_extra_datum_inputs):
        try:
            data = EmployeeExtraModel(**employee_extra_datum_inputs)
            self.db.add(data)
            self.db.commit()
            return "Registro agregado"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(EmployeeExtraModel).filter(EmployeeExtraModel.rut == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, rut, employee_extra_datum_inputs):
        employee_extra =  self.db.query(EmployeeExtraModel).filter(EmployeeExtraModel.rut == rut).first()
        
        if 'extreme_zone_id' in employee_extra_datum_inputs and employee_extra_datum_inputs['extreme_zone_id'] is not None:
            employee_extra.extreme_zone_id = employee_extra_datum_inputs['extreme_zone_id']

        if 'employee_type_id' in employee_extra_datum_inputs and employee_extra_datum_inputs['extreme_zone_id'] is not None:
            employee_extra.employee_type_id = employee_extra_datum_inputs['employee_type_id']

        if 'young_job_status_id' in employee_extra_datum_inputs and employee_extra_datum_inputs['young_job_status_id'] is not None:
            employee_extra.young_job_status_id = employee_extra_datum_inputs['young_job_status_id']

        if 'be_paid_id' in employee_extra_datum_inputs and employee_extra_datum_inputs['be_paid_id'] is not None:
            employee_extra.be_paid_id = employee_extra_datum_inputs['be_paid_id']

        if 'pensioner_id' in employee_extra_datum_inputs and employee_extra_datum_inputs['pensioner_id'] is not None:
            employee_extra.pensioner_id = employee_extra_datum_inputs['pensioner_id']

        if 'disability_id' in employee_extra_datum_inputs and employee_extra_datum_inputs['disability_id'] is not None:
            employee_extra.disability_id = employee_extra_datum_inputs['disability_id']

        if 'suplemental_health_insurance_id' in employee_extra_datum_inputs and employee_extra_datum_inputs['suplemental_health_insurance_id'] is not None:
            employee_extra.suplemental_health_insurance_id = employee_extra_datum_inputs['suplemental_health_insurance_id']

        if 'progressive_vacation_level_id' in employee_extra_datum_inputs and employee_extra_datum_inputs['progressive_vacation_level_id'] is not None:
            employee_extra.progressive_vacation_level_id = employee_extra_datum_inputs['progressive_vacation_level_id']

        if 'recognized_years' in employee_extra_datum_inputs and employee_extra_datum_inputs['recognized_years'] is not None:
            employee_extra.recognized_years = employee_extra_datum_inputs['recognized_years']

        if 'progressive_vacation_status_id' in employee_extra_datum_inputs and employee_extra_datum_inputs['progressive_vacation_status_id'] is not None:
            employee_extra.progressive_vacation_status_id = employee_extra_datum_inputs['progressive_vacation_status_id']

        if 'progressive_vacation_date' in employee_extra_datum_inputs and employee_extra_datum_inputs['progressive_vacation_date'] is not None:
            employee_extra.progressive_vacation_date = employee_extra_datum_inputs['progressive_vacation_date']

        employee_extra.update_date = datetime.now()

        self.db.add(employee_extra)

        try:
            self.db.commit()

            return 1
        except Exception as e:
            return 0