from app.backend.db.models import OldEmployeeLaborDatumModel, RegionModel, HealthModel, CommuneModel, CivilStateModel, JobPositionModel, BranchOfficeModel, PentionModel
from datetime import datetime
from app.backend.classes.helper_class import HelperClass
import json

class OldEmployeeLaborDatumClass:
    def __init__(self, db):
        self.db = db

    def get(self, field, value):
        try:
            
            data = self.db.query(OldEmployeeLaborDatumModel, RegionModel, HealthModel, CommuneModel, CivilStateModel, JobPositionModel, BranchOfficeModel, PentionModel). \
                outerjoin(RegionModel, RegionModel.id == OldEmployeeLaborDatumModel.region_id). \
                outerjoin(CommuneModel, CommuneModel.id == OldEmployeeLaborDatumModel.commune_id). \
                outerjoin(CivilStateModel, CivilStateModel.id == OldEmployeeLaborDatumModel.civil_state_id). \
                outerjoin(JobPositionModel, JobPositionModel.id == OldEmployeeLaborDatumModel.job_position_id). \
                outerjoin(BranchOfficeModel, BranchOfficeModel.id == OldEmployeeLaborDatumModel.branch_office_id). \
                outerjoin(PentionModel, PentionModel.id == OldEmployeeLaborDatumModel.pention_id). \
                outerjoin(HealthModel, HealthModel.id == OldEmployeeLaborDatumModel.health_id). \
                filter(getattr(OldEmployeeLaborDatumModel, field) == value).first()

            if data:
                employee_labor_data = data[0]
                region = data[1]
                health = data[2]
                commune = data[3]
                civil_state = data[4]
                job_position = data[5]
                branch_office = data[6]
                pention = data[7]

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

                entrance_pention = employee_labor_data.entrance_pention

                entrance_company = employee_labor_data.entrance_company

                entrance_health = employee_labor_data.entrance_health

                exit_company = employee_labor_data.exit_company

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

                if exit_company and exit_company != '0000-00-00':
                    formatted_exit_company = datetime.strptime(exit_company, '%Y-%m-%d').date()
                    formatted_exit_company_str = formatted_exit_company.strftime('%Y-%m-%d')
                else:
                    formatted_exit_company = None
                    formatted_exit_company_str = None

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
                    "employee_type_id": employee_labor_data.employee_type_id,
                    "regime_id": employee_labor_data.regime_id,
                    "status_id": employee_labor_data.status_id,
                    "health_payment_id": employee_labor_data.health_payment_id,
                    "entrance_pention": formatted_entrance_pention_str,
                    "entrance_company": formatted_entrance_company_str,
                    "entrance_health": formatted_entrance_health_str,
                    "exit_company": formatted_exit_company_str,
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
                    "PentionModel": serialized_pention
                })

                return serialized_result
            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, old_employee_labor_datum_inputs):
        numeric_rut = HelperClass().numeric_rut(str(old_employee_labor_datum_inputs['rut']))

        employee_labor_datum = OldEmployeeLaborDatumModel()
        employee_labor_datum.rut = numeric_rut
        employee_labor_datum.visual_rut = old_employee_labor_datum_inputs['visual_rut']
        employee_labor_datum.contract_type_id = old_employee_labor_datum_inputs['contract_type_id']
        employee_labor_datum.branch_office_id = old_employee_labor_datum_inputs['branch_office_id']
        employee_labor_datum.address = old_employee_labor_datum_inputs['address']
        employee_labor_datum.region_id = old_employee_labor_datum_inputs['region_id']
        employee_labor_datum.commune_id = old_employee_labor_datum_inputs['commune_id']
        employee_labor_datum.civil_state_id = old_employee_labor_datum_inputs['civil_state_id']
        employee_labor_datum.health_id = old_employee_labor_datum_inputs['health_id']
        employee_labor_datum.pention_id = old_employee_labor_datum_inputs['pention_id']
        employee_labor_datum.job_position_id = old_employee_labor_datum_inputs['job_position_id']
        employee_labor_datum.employee_type_id = old_employee_labor_datum_inputs['employee_type_id']
        employee_labor_datum.regime_id = old_employee_labor_datum_inputs['regime_id']
        employee_labor_datum.status_id = old_employee_labor_datum_inputs['status_id']
        employee_labor_datum.health_payment_id = old_employee_labor_datum_inputs['health_payment_id']
        employee_labor_datum.apv_payment_type_id = old_employee_labor_datum_inputs['apv_payment_type_id']
        employee_labor_datum.entrance_pention = old_employee_labor_datum_inputs['entrance_pention']
        employee_labor_datum.entrance_company = old_employee_labor_datum_inputs['entrance_company']
        employee_labor_datum.entrance_health = old_employee_labor_datum_inputs['entrance_health']
        employee_labor_datum.exit_company  = old_employee_labor_datum_inputs['exit_company']
        employee_labor_datum.salary = old_employee_labor_datum_inputs['salary']
        employee_labor_datum.collation = old_employee_labor_datum_inputs['collation']
        employee_labor_datum.locomotion = old_employee_labor_datum_inputs['locomotion']
        employee_labor_datum.extra_health_amount = old_employee_labor_datum_inputs['extra_health_amount']
        employee_labor_datum.apv_amount = old_employee_labor_datum_inputs['apv_amount']
        employee_labor_datum.added_date = datetime.now()
        

        self.db.add(employee_labor_datum)

        try:
            self.db.commit()

            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"