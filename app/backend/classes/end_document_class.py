from datetime import datetime
from app.backend.db.models import DocumentEmployeeModel
from app.backend.classes.hr_setting_class import HrSettingClass
from app.backend.classes.employee_labor_datum_class import EmployeeLaborDatumClass
from app.backend.db.models import EndDocumentModel
from app.backend.classes.helper_class import HelperClass
import json
from sqlalchemy import desc


class EndDocumentClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, rut):
        try:
            data = self.db.query(
                DocumentEmployeeModel.status_id,
                EndDocumentModel.causal_id,
                EndDocumentModel.fertility_proportional_days,
                EndDocumentModel.fertility_proportional,
                EndDocumentModel.indemnity_years_service,
                EndDocumentModel.voluntary_indemnity,
                EndDocumentModel.substitute_compensation,
                EndDocumentModel.total,
                DocumentEmployeeModel.added_date,
                DocumentEmployeeModel.support,
                DocumentEmployeeModel.rut,
                DocumentEmployeeModel.id). \
            outerjoin(
                EndDocumentModel, EndDocumentModel.document_employee_id == DocumentEmployeeModel.id). \
            filter(
                DocumentEmployeeModel.rut == rut,
                DocumentEmployeeModel.document_type_id == 22
            ).order_by(desc(DocumentEmployeeModel.id)).all()
            print(str(data))
            if not data:
                return 0

            # Convertir los resultados a una lista de diccionarios
            serialized_data = []
            for row in data:
                serialized_row = {
                    "status_id": row.status_id,
                    "causal_id": row.causal_id,
                    "fertility_proportional_days": row.fertility_proportional_days,
                    "fertility_proportional": row.fertility_proportional,
                    "indemnity_years_service": row.indemnity_years_service,
                    "voluntary_indemnity": row.voluntary_indemnity,
                    "substitute_compensation": row.substitute_compensation,
                    "total": row.total,
                    "added_date": row.added_date.strftime('%Y-%m-%d') if row.added_date else None,
                    "support": row.support,
                    "rut": row.rut,
                    "id": row.id,
                }
                serialized_data.append(serialized_row)


            return json.dumps(serialized_data)
        except Exception as e:
            error_message = str(e)
            return json.dumps({"error": f"Error: {error_message}"})


    # Funcion para obtener la indemnizacion por años de servicio
    def indemnity_years(self, indemnity_year_inputs):
        try:
            hr_settings = HrSettingClass(self.db).get()
            employee_labor_datum = EmployeeLaborDatumClass(self.db).get("rut", indemnity_year_inputs['rut'])
            employee_labor_datum = json.loads(employee_labor_datum)
            gratification = HelperClass.gratification(employee_labor_datum["EmployeeLaborDatumModel"]["salary"])
            if gratification > hr_settings.top_gratification:
                gratification = hr_settings.top_gratification
            years = HelperClass().get_end_document_total_years(employee_labor_datum["EmployeeLaborDatumModel"]["entrance_company"], indemnity_year_inputs['exit_company'] )

            if years > 11:
                years = 11

            result = (int(employee_labor_datum["EmployeeLaborDatumModel"]["salary"]) + 
                    int(employee_labor_datum["EmployeeLaborDatumModel"]["collation"]) + 
                    int(employee_labor_datum["EmployeeLaborDatumModel"]["locomotion"]) + 
                    int(gratification)) * (years) 
            
            return result
        
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    # Funcion para Calcular la  Indemnización Sustitutivo de Aviso Previo      
    def substitute_compensation(self, substitute_compesation_inputs):
        try:
            hr_settings = HrSettingClass(self.db).get()
            employee_labor_datum = EmployeeLaborDatumClass(self.db).get("rut", substitute_compesation_inputs['rut'])
            employee_labor_datum = json.loads(employee_labor_datum)

            gratification = HelperClass.gratification(employee_labor_datum["EmployeeLaborDatumModel"]["salary"])
            if gratification > hr_settings.top_gratification:
                gratification = hr_settings.top_gratification

            result = (int(employee_labor_datum["EmployeeLaborDatumModel"]["salary"])  
                    + int(employee_labor_datum["EmployeeLaborDatumModel"]["collation"]) 
                    + int(employee_labor_datum["EmployeeLaborDatumModel"]["locomotion"])  
                    + int(gratification))
           
            return result
        
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        

    # Funcion para calcular la indemnizacion para el calculo de vacaciones proporcionales
    def fertility_proportional(self, fertility_proportional_inputs):
        employee_labor_datum = EmployeeLaborDatumClass(self.db).get("rut", fertility_proportional_inputs['rut'])
        employee_labor_datum = json.loads(employee_labor_datum)
        
        start_date = fertility_proportional_inputs['exit_company']
        end_date = HelperClass.add_business_days(start_date, fertility_proportional_inputs['balance'], fertility_proportional_inputs['number_holidays'])
        end_date_split = HelperClass().split(str(end_date), " ")
        weekends_between_dates = HelperClass.count_weekends(start_date, end_date_split[0])
        total = float(fertility_proportional_inputs['balance']) + float(weekends_between_dates) + float(fertility_proportional_inputs['number_holidays'])

        vacation_day_value = HelperClass.vacation_day_value(employee_labor_datum["EmployeeLaborDatumModel"]["salary"])

        result = round(int(vacation_day_value) * round(total, 2))

        if result < 0:
            result = 0

        return result
    

    # Funcion para calcular el total de dias de vacaciones
    def total_vacations(self, fertility_proportional_inputs):
        start_date = fertility_proportional_inputs['exit_company']
        end_date = HelperClass.add_business_days(start_date, fertility_proportional_inputs['balance'], fertility_proportional_inputs['number_holidays'])

        end_date_split = HelperClass().split(str(end_date), " ")
        weekends_between_dates = HelperClass.count_weekends(start_date, end_date_split[0])

        total = float(fertility_proportional_inputs['balance']) + float(weekends_between_dates) + float(fertility_proportional_inputs['number_holidays'])

        result = float(total)

        if result < 0:
            result = 0

        return result
    
    def store(self, end_documents_inputs, document_id):
        try:
            end_document = EndDocumentModel()
            end_document.document_employee_id = document_id
            end_document.causal_id = end_documents_inputs['causal_id']
            end_document.rut = end_documents_inputs['rut']
            end_document.fertility_proportional_days = end_documents_inputs['fertility_proportional_days']
            end_document.voluntary_indemnity = end_documents_inputs['voluntary_indemnity']
            end_document.indemnity_years_service = end_documents_inputs['indemnity_years_service']
            end_document.substitute_compensation = end_documents_inputs['substitute_compensation']
            end_document.fertility_proportional = end_documents_inputs['fertility_proportional']
            end_document.total = end_documents_inputs['total']
            end_document.added_date = datetime.now()

            self.db.add(end_document)
            self.db.commit()
            
            return end_document.id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
