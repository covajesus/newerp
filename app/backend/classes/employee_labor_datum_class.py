from app.backend.db.models import EmployeeLaborDatumModel, HealthModel, ContractTypeModel, PentionModel, EmployeeModel, CommuneModel, RegionModel, CivilStateModel, JobPositionModel, BranchOfficeModel
from datetime import datetime
from app.backend.classes.helper_class import HelperClass
import json


class EmployeeLaborDatumClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(EmployeeLaborDatumModel).order_by(EmployeeLaborDatumModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    # Funcion para obtener a todos los empleados por sucursal
    def get_all_by_branch_office(self, branch_office_id):
        try:
            results = self.db.query(EmployeeModel, EmployeeLaborDatumModel.employee_type_id).\
                outerjoin(EmployeeLaborDatumModel, EmployeeLaborDatumModel.rut == EmployeeModel.rut).\
                filter(EmployeeLaborDatumModel.branch_office_id == branch_office_id).\
                order_by(EmployeeModel.id).all()
            if not results:
                return "No data found"
            
            data = []
            for employee, employee_type_id in results:
                employee.employee_type_id = employee_type_id
                data.append(employee)
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def get(self, field, value):
        try:
            data = self.db.query(EmployeeLaborDatumModel, RegionModel, HealthModel, CommuneModel, CivilStateModel, JobPositionModel, BranchOfficeModel, PentionModel, ContractTypeModel). \
                outerjoin(RegionModel, RegionModel.id == EmployeeLaborDatumModel.region_id). \
                outerjoin(CommuneModel, CommuneModel.id == EmployeeLaborDatumModel.commune_id). \
                outerjoin(CivilStateModel, CivilStateModel.id == EmployeeLaborDatumModel.civil_state_id). \
                outerjoin(JobPositionModel, JobPositionModel.id == EmployeeLaborDatumModel.job_position_id). \
                outerjoin(BranchOfficeModel, BranchOfficeModel.id == EmployeeLaborDatumModel.branch_office_id). \
                outerjoin(PentionModel, PentionModel.id == EmployeeLaborDatumModel.pention_id). \
                outerjoin(HealthModel, HealthModel.id == EmployeeLaborDatumModel.health_id). \
                outerjoin(ContractTypeModel, ContractTypeModel.id == EmployeeLaborDatumModel.contract_type_id). \
                filter(getattr(EmployeeLaborDatumModel, field) == value).first()

            if data:
                employee_labor_data = data[0]
                region = data[1]
                health = data[2]
                commune = data[3]
                civil_state = data[4]
                job_position = data[5]
                branch_office = data[6]
                pention = data[7]
                contract_type = data[8]

                serialized_region = {
                    "id": region.id,
                    "region": region.region,
                    "region_remuneration_code": region.region_remuneration_code,
                }

                serialized_health = {
                    "id": health.id,
                    "health_remuneration_code": health.health_remuneration_code,
                    "health": health.health,
                    "rut": health.rut,
                    "social_law": health.social_law,
                }

                serialized_commune = {
                    "id": commune.id,
                    "region_id": commune.region_id,
                    "commune": commune.commune,
                }

                serialized_civil_state = {
                    "id": civil_state.id,
                    "civil_state": civil_state.civil_state,
                }

                serialized_job_position = {
                    "id": job_position.id,
                    "job_position": job_position.job_position,
                    "functions": job_position.functions,
                }

                serialized_branch_office = {
                    "id": branch_office.id,
                    "branch_office": branch_office.branch_office,
                    "address": branch_office.address,
                    "region_id": branch_office.region_id,
                    "commune_id": branch_office.commune_id,
                    "segment_id": branch_office.segment_id,
                    "zone_id": branch_office.zone_id,
                    "principal_id": branch_office.principal_id,
                    "status_id": branch_office.status_id,
                    "visibility_id": branch_office.visibility_id,
                    "opening_date": branch_office.opening_date,
                    "dte_code": branch_office.dte_code,
                }

                serialized_pention = {
                    "id": pention.id,
                    "pention": pention.pention,
                    "social_law": pention.social_law_code,
                    "rut": pention.rut,
                    "amount": pention.amount,
                    "previred_code": pention.previred_code,
                }

                serialized_contract_type = {
                    "id": contract_type.id,
                    "contract_type": contract_type.contract_type
                }

                entrance_pention = employee_labor_data.entrance_pention

                entrance_company = employee_labor_data.entrance_company

                entrance_health = employee_labor_data.entrance_health

                if entrance_pention and entrance_pention != '0000-00-00' and entrance_pention != None:
                    formatted_entrance_pention = datetime.strptime(entrance_pention, '%Y-%m-%d').date()
                    formatted_entrance_pention_str = formatted_entrance_pention.strftime('%Y-%m-%d')
                else:
                    formatted_entrance_pention = None
                    formatted_entrance_pention_str = None

                if entrance_company and entrance_company != '0000-00-00':
                    formatted_entrance_company = datetime.strptime(entrance_company, '%Y-%m-%d').date()
                    formatted_entrance_company_str = formatted_entrance_company.strftime('%Y-%m-%d')
                else:
                    formatted_entrance_company = None
                    formatted_entrance_company_str = None

                if entrance_health and entrance_health != '0000-00-00':
                    formatted_entrance_health = datetime.strptime(entrance_health, '%Y-%m-%d').date()
                    formatted_entrance_health_str = formatted_entrance_health.strftime('%Y-%m-%d')
                else:
                    formatted_entrance_health = None
                    formatted_entrance_health_str = None

                serialized_employee_labor_data = {
                    "id": employee_labor_data.id,
                    "rut": employee_labor_data.rut,
                    "contract_type_id": employee_labor_data.contract_type_id,
                    "branch_office_id": employee_labor_data.branch_office_id,
                    "address": employee_labor_data.address,
                    "region_id": region.id if region else None,
                    "region_name": region.region if region else None,
                    "commune_id": commune.id if commune else None,
                    "commune_name": commune.commune if commune else None,
                    "civil_state_id": civil_state.id if civil_state else None,
                    "civil_state_name": civil_state.civil_state if civil_state else None,
                    "health_id": health.id if health else None,
                    "health_name": health.health if health else None,
                    "pention_id": pention.id if pention else None,
                    "pention_name": pention.pention if pention else None,
                    "job_position_id": job_position.id if job_position else None,
                    "job_position_name": job_position.job_position if job_position else None,
                    "extra_health_payment_type_id": employee_labor_data.extra_health_payment_type_id,
                    "employee_type_id": employee_labor_data.employee_type_id,
                    "regime_id": employee_labor_data.regime_id,
                    "status_id": employee_labor_data.status_id,
                    "health_payment_id": employee_labor_data.health_payment_id,
                    "entrance_pention": formatted_entrance_pention_str,
                    "entrance_company": formatted_entrance_company_str,
                    "entrance_health": formatted_entrance_health_str,
                    "salary": employee_labor_data.salary,
                    "collation": employee_labor_data.collation,
                    "locomotion": employee_labor_data.locomotion,
                    "extra_health_amount": employee_labor_data.extra_health_amount,
                    "apv_payment_type_id": employee_labor_data.apv_payment_type_id,
                    "apv_amount": employee_labor_data.apv_amount
                }


                # Convierte el resultado a una cadena JSON
                serialized_result = json.dumps({
                    "EmployeeLaborDatumModel": serialized_employee_labor_data,
                    "RegionModel": serialized_region,
                    "HealthModel": serialized_health,
                    "CommuneModel": serialized_commune,
                    "CivilStateModel": serialized_civil_state,
                    "JobPositionModel": serialized_job_position,
                    "BranchOfficeModel": serialized_branch_office,
                    "PentionModel": serialized_pention,
                    "ContractTypeModel": serialized_contract_type
                })

                return serialized_result
            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, employee_labor_datum_inputs):
        numeric_rut = HelperClass().numeric_rut(str(employee_labor_datum_inputs['rut']))

        employee_labor_datum = EmployeeLaborDatumModel()
        employee_labor_datum.rut = numeric_rut
        employee_labor_datum.visual_rut = employee_labor_datum_inputs['rut']
        employee_labor_datum.status_id = 1
        employee_labor_datum.added_date = datetime.now()

        self.db.add(employee_labor_datum)

        try:
            self.db.commit()

            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, rut):
        try:
            data = self.db.query(EmployeeLaborDatumModel).filter(EmployeeLaborDatumModel.rut == rut).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, employee_labor_datum_inputs):
        employee_labor_datum = self.db.query(EmployeeLaborDatumModel).filter(EmployeeLaborDatumModel.rut == id).first()

        if 'rut' in employee_labor_datum_inputs and employee_labor_datum_inputs['rut'] is not None:
            numeric_rut = HelperClass().numeric_rut(str(employee_labor_datum_inputs['rut']))
            employee_labor_datum.rut =  numeric_rut
            employee_labor_datum.visual_rut = employee_labor_datum_inputs['rut']
        
        if 'contract_type_id' in employee_labor_datum_inputs and employee_labor_datum_inputs['contract_type_id'] is not None:
            employee_labor_datum.contract_type_id = employee_labor_datum_inputs['contract_type_id']
         
        if 'branch_office_id' in employee_labor_datum_inputs and employee_labor_datum_inputs['branch_office_id'] is not None:
             employee_labor_datum.branch_office_id = employee_labor_datum_inputs['branch_office_id']
        
        if 'address' in employee_labor_datum_inputs and employee_labor_datum_inputs['address'] is not None:
                 employee_labor_datum.address = employee_labor_datum_inputs['address']

        if 'region_id' in employee_labor_datum_inputs and employee_labor_datum_inputs['region_id'] is not None:
            employee_labor_datum.region_id = employee_labor_datum_inputs['region_id']
        
        if 'commune_id' in employee_labor_datum_inputs and employee_labor_datum_inputs['commune_id'] is not None:
            employee_labor_datum.commune_id = employee_labor_datum_inputs['commune_id']
        
        if 'civil_state_id' in employee_labor_datum_inputs and employee_labor_datum_inputs['civil_state_id'] is not None:
            employee_labor_datum.civil_state_id = employee_labor_datum_inputs['civil_state_id']
        
        if 'health_id' in employee_labor_datum_inputs and employee_labor_datum_inputs['health_id'] is not None:
            employee_labor_datum.health_id = employee_labor_datum_inputs['health_id']
        
        if 'pention_id' in employee_labor_datum_inputs and employee_labor_datum_inputs['pention_id'] is not None:
            employee_labor_datum.pention_id = employee_labor_datum_inputs['pention_id']

        if 'job_position_id' in employee_labor_datum_inputs and employee_labor_datum_inputs['job_position_id'] is not None:
            employee_labor_datum.job_position_id = employee_labor_datum_inputs['job_position_id']

        if 'employee_type_id' in employee_labor_datum_inputs and employee_labor_datum_inputs['employee_type_id'] is not None:
            employee_labor_datum.employee_type_id = employee_labor_datum_inputs['employee_type_id']

        if 'regime_id' in employee_labor_datum_inputs and employee_labor_datum_inputs['regime_id'] is not None:
            employee_labor_datum.regime_id = employee_labor_datum_inputs['regime_id']

        if 'entrance_pention' in employee_labor_datum_inputs and employee_labor_datum_inputs['entrance_pention'] is not None:
            employee_labor_datum.entrance_pention = employee_labor_datum_inputs['entrance_pention']

        if 'entrance_company' in employee_labor_datum_inputs and employee_labor_datum_inputs['entrance_company'] is not None:
            employee_labor_datum.entrance_company = employee_labor_datum_inputs['entrance_company']

        if 'entrance_health' in employee_labor_datum_inputs and employee_labor_datum_inputs['entrance_health'] is not None:
            employee_labor_datum.entrance_health = employee_labor_datum_inputs['entrance_health']

        if 'salary' in employee_labor_datum_inputs and employee_labor_datum_inputs['salary'] is not None:
            employee_labor_datum.salary = employee_labor_datum_inputs['salary']

        if 'collation' in employee_labor_datum_inputs and employee_labor_datum_inputs['collation'] is not None:
            employee_labor_datum.collation = employee_labor_datum_inputs['collation']

        if 'locomotion' in employee_labor_datum_inputs and employee_labor_datum_inputs['locomotion'] is not None:
            employee_labor_datum.locomotion = employee_labor_datum_inputs['locomotion']

        if 'extra_health_payment_type_id' in employee_labor_datum_inputs and employee_labor_datum_inputs['extra_health_payment_type_id'] is not None:
            employee_labor_datum.extra_health_payment_type_id = employee_labor_datum_inputs['extra_health_payment_type_id']

        if 'extra_health_amount' in employee_labor_datum_inputs and employee_labor_datum_inputs['extra_health_amount'] is not None:
            employee_labor_datum.extra_health_amount = employee_labor_datum_inputs['extra_health_amount']

        if 'apv_payment_type_id' in employee_labor_datum_inputs and employee_labor_datum_inputs['apv_payment_type_id'] is not None:
            employee_labor_datum.apv_payment_type_id = employee_labor_datum_inputs['apv_payment_type_id']

        if 'apv_amount' in employee_labor_datum_inputs and employee_labor_datum_inputs['apv_amount'] is not None:
            employee_labor_datum.apv_amount = employee_labor_datum_inputs['apv_amount']

        employee_labor_datum.updated_date = datetime.now()

        self.db.add(employee_labor_datum)

        try:
            self.db.commit()

            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

        return 1
    
    def active_employee_total(self):
        total = self.db.query(EmployeeModel).count()

        return total
    
    def distribution_totals(self):
        full_time_total = self.db.query(EmployeeLaborDatumModel, EmployeeModel). \
                join(EmployeeModel, EmployeeModel.rut == EmployeeLaborDatumModel.rut). \
                filter(EmployeeLaborDatumModel.employee_type_id == 1).count()
        
        part_time_total = self.db.query(EmployeeLaborDatumModel, EmployeeModel). \
                join(EmployeeModel, EmployeeModel.rut == EmployeeLaborDatumModel.rut). \
                filter(EmployeeLaborDatumModel.employee_type_id == 2).count()

        totals = [
            {'schedule': 'Full-Time', 'Total': full_time_total},
            {'schedule': 'Part-Time', 'Total': part_time_total}
        ]
    
        return totals