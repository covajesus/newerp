from pydantic import BaseModel, Field
from fastapi import UploadFile, File
from typing import Union, List, Dict, Optional
from datetime import datetime
from decimal import Decimal
from fastapi import Form
from typing import List

class Alert(BaseModel):
    alert_type_id: int
    status_id: int
    rut: int

class UpdateAlert(BaseModel):
    status_id: int = None

class BranchOffice(BaseModel):
    branch_office: str
    address: str
    region_id: int
    commune_id: int
    segment_id: int
    zone_id: int
    principal_id: int
    status_id: int
    visibility_id: int
    opening_date: str
    dte_code: int
    principal_supervisor: int
    added_date: datetime
    updated_date: Union[datetime, None]

class Employee(BaseModel):
    rut: str
    names: str
    father_lastname: str
    mother_lastname: str
    gender_id: int
    nationality_id: int
    personal_email: str
    cellphone: str
    born_date: str
    privilege: Union[int, None]
    added_date: datetime
    updated_date: Union[datetime, None]

class OldEmployee(BaseModel):
    end_document_type_id: int
    rut: int
    visual_rut:str
    names: str
    father_lastname: str
    mother_lastname: str
    gender_id: int
    nationality_id: int
    personal_email: str
    cellphone: str
    born_date: str
    privilege: Union[int, None]

class UpdateBranchOffice(BaseModel):
    branch_office: str = None
    address: str = None
    region_id: int = None
    commune_id: int = None
    segment_id: int = None
    zone_id: int = None
    principal_id: int = None
    status_id: int = None
    visibility_id: int = None
    opening_date: str = None
    dte_code: int = None
    principal_supervisor: int = None
    updated_date: Union[datetime, None]

class Gender(BaseModel):
    gender: str
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateGender(BaseModel):
    gender: str = None
    updated_date: Union[datetime, None]

class Nationality(BaseModel):
    nationality: str
    previred_code: int
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateNationality(BaseModel):
    nationality: str = None
    previred_code: int = None
    updated_date: Union[datetime, None]

class Pention(BaseModel):
    pention: str
    social_law: int
    rut: str
    amount: str
    previred_code: int
    added_date: datetime
    updated_date: Union[datetime, None]

class Contact(BaseModel):
    name: str
    lastname: str
    email: str
    phone: str
    subject: str
    message: str

class UpdatePention(BaseModel):
    pention: str = None
    social_law: int = None
    rut: str = None
    amount: str = None
    previred_code: int = None
    updated_date: str = None

class Bank(BaseModel):
    visibility_id: int
    bank: str
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateBank(BaseModel):
    visibility_id: int = None
    bank: str = None

class Segment(BaseModel):
    segment: str
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateSegment(BaseModel):
    segment: str = None
    updated_date: Union[datetime, None]

class AccountType(BaseModel):
    id: int
    account_type: str
    added_date: str
    updated_date: str

class UpdateAccountType(BaseModel):
    account_type: str = None
    updated_date: str = None

class Region(BaseModel):
    id: int
    region: str
    region_remuneration_code: int
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateRegion(BaseModel):
    id: int = None
    region: str = None
    region_remuneration_code: int = None
    updated_date: Union[datetime, None]
    
class UpdateEmployee(BaseModel):
    rut: str = None
    names: str = None
    father_lastname: str = None
    mother_lastname: str = None
    gender_id: int = None
    nationality_id: int = None
    personal_email: str = None
    cellphone: str = None
    born_date: str = None

class UserLogin(BaseModel):
    rol_id: Union[int, None]
    clock_rol_id: Union[int, None]
    status_id: Union[int, None]
    rut: Union[int, None]
    visual_rut: Union[str, None]
    nickname: Union[str, None]
    hashed_password: Union[str, None]
    disabled: Union[int, None]

class RecoverUser(BaseModel):
    rut: str
    email: str

class User(BaseModel):
    rol_id: int
    clock_rol_id: int
    status_id: int
    rut: str
    names: str
    father_lastname: str
    password: str
    disabled: int
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateUser(BaseModel):
    clock_rol_id: int = None
    rut: str = None
    names: str = None
    father_lastname: str = None

class Uniform(BaseModel):
    uniform_type_id: int
    rut: int
    size: str
    delivered_date: str
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateUniform(BaseModel):
    uniform_type_id: int = None
    rut: int = None
    delivered_date: str = None
    updated_date: Union[datetime, None]

class EmployeeLaborDatum(BaseModel):
    rut: str
    added_date: datetime
    updated_date: Union[datetime, None]

class expirationDatum(BaseModel):
    rut: str

class OldEmployeeLaborDatum(BaseModel):
    end_document_type_id: int
    rut: str = None
    visual_rut: str = None
    contract_type_id: int = None
    branch_office_id: int = None
    address: str = None
    region_id: int = None
    commune_id: int = None
    civil_state_id: int = None
    health_id: int = None
    pention_id: int = None
    job_position_id: int = None
    employee_type_id: int = None
    regime_id: int = None
    status_id: int = None 
    health_payment_id: int = None
    extra_health_payment_type_id: int = None
    apv_payment_type_id: int = None
    entrance_pention: str = None
    entrance_company: str = None
    entrance_health: str = None
    exit_company : str = None
    salary: int = None
    collation: int = None
    locomotion: int = None
    extra_health_amount: str = None
    apv_amount: str = None

class UpdateEmployeeLaborDatum(BaseModel):
    rut: str = None
    contract_type_id: int = None
    branch_office_id: int = None
    address: str = None
    region_id: int = None
    commune_id: int = None
    civil_state_id: int = None
    health_id: int = None
    pention_id: Union[int, None]
    job_position_id: int = None
    employee_type_id: int = None
    regime_id: int = None
    health_payment_id: int = None
    entrance_pention: Union[str, None]
    entrance_company: str = None
    entrance_health: Union[str, None]
    salary: int = None
    collation: int = None
    locomotion: int = None
    extra_health_payment_type_id: Union[int, None]
    extra_health_amount: str = None
    apv_payment_type_id: Union[int, None]
    apv_amount: Union[int, None]

class EmployeeExtra(BaseModel):
    rut: int
    added_date: datetime
    updated_date: Union[datetime, None]

class OldEmployeeExtra(BaseModel):
    rut: int 
    extreme_zone_id : int = None   
    employee_type_id: int = None
    young_job_status_id: int = None
    be_paid_id : int = None 
    suplemental_health_insurance_id: int = None
    disability_id: int = None
    pensioner_id: int = None
    progressive_vacation_status_id: int = None
    progressive_vacation_date: Union[str, None]
    recognized_years: Union[int, None]

class GetEmployeeExtra(BaseModel):
    rut: int

class UpdateEmployeeExtra(BaseModel):
    extreme_zone_id: int = None
    employee_type_id: int = None
    young_job_status_id: int = None
    be_paid_id: int = None
    suplemental_health_insurance_id: int = None
    pensioner_id: int = None
    disability_id: int = None
    suplemental_health_insurance_id: int = None
    progressive_vacation_level_id: int = None
    recognized_years: Union[int, None]
    progressive_vacation_status_id: int = None
    progressive_vacation_date: Union[str, None]
    updated_date: Union[datetime, None]

class AlertType(BaseModel):
    alert_type: str
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateAlertType(BaseModel):
    alert_type: str = None
    updated_date: Union[datetime, None]

class GenerateHonorary(BaseModel):
    reason_id: int
    branch_office_id: int
    foreigner_id: int
    bank_id: int
    schedule_id: int
    region_id: int
    commune_id: int
    requested_by: int
    status_id: int
    accountability_status_id: int
    employee_to_replace: int
    rut: str
    full_name: str
    email: str
    address: str
    account_number: str
    start_date: str
    end_date: str
    observation: str
    amount: int
    observation: str

class Honorary(BaseModel):
    reason_id: int
    branch_office_id: int
    foreigner_id: int
    bank_id: int
    schedule_id: int
    region_id: int
    commune_id: int
    requested_by: int
    status_id: int
    accountability_status_id: int
    employee_to_replace: int
    rut: str
    full_name: str
    email: str
    address: str
    account_number: str
    start_date: str
    end_date: str
    observation: str
    amount: int
    observation: str

class PayrollSecondCategoryTax(BaseModel):
    period: str
    since_1: str
    until_1: str
    factor_1: str
    discount_1: str
    since_2: str
    until_2: str
    factor_2: str
    discount_2: str
    since_3: str
    until_3: str
    factor_3: str
    discount_3: str
    since_4: str
    until_4: str
    factor_4: str
    discount_4: str

    @classmethod
    def as_form(cls, 
                period: str = Form(),
                since_1: str = Form(),
                until_1: str = Form(), 
                factor_1: str = Form(),
                discount_1: str = Form(),
                since_2: str = Form(),
                until_2: str = Form(),
                factor_2: str = Form(),
                discount_2: str = Form(),
                since_3: str = Form(),
                until_3: str = Form(),
                factor_3: str = Form(),
                discount_3: str = Form(),
                since_4: str = Form(),
                until_4: str = Form(),
                factor_4: str = Form(),
                discount_4: str = Form()
                ):
        return cls(period=period, since_1=since_1, until_1=until_1, factor_1=factor_1, discount_1=discount_1, since_2=since_2, until_2=until_2, factor_2=factor_2, discount_2=discount_2, since_3=since_3, until_3=until_3, factor_3=factor_3, discount_3=discount_3, since_4=since_4, until_4=until_4, factor_4=factor_4, discount_4=discount_4)
   
class UpdateHonorary(BaseModel):
    reason_id: int = None
    branch_office_id: int = None
    foreigner_id: int = None
    bank_id: int = None
    schedule_id: int = None
    region_id: int = None
    commune_id: int = None
    requested_by: int = None
    status_id: int = None
    accountability_status_id: int = None
    employee_to_replace: int = None
    rut: str = None
    full_name: str = None
    email: str = None
    address: str = None
    account_number: str = None
    start_date: str = None
    end_date: str = None
    amount: str = None
    observation: str = None

class UniformType(BaseModel):
    uniform_type: str
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateUniformType(BaseModel):
    uniform_type: str = None
    updated_date: Union[datetime, None]

class JobPosition(BaseModel):
    job_position: str
    functions: str
    added_date: datetime
    updated_date: Union[datetime, None]


class PayrollItem(BaseModel):
    item_type_id: int
    classification_id: int
    order_id: int
    item: str
    salary_settlement_name: str
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateJobPosition(BaseModel):
    job_position: str = None
    functions: str = None
    updated_date: Union[datetime, None]

class PatologyType(BaseModel):
    patology_type: str
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdatePatologyType(BaseModel):
    patology_type: str = None
    updated_date: Union[datetime, None]

class CivilState(BaseModel):
    civil_state: str
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateCivilState(BaseModel):
    civil_state: str = None
    updated_date: Union[datetime, None]

class DocumentType(BaseModel):
    document_type: str
    document_group_id: int
    order: int
    added_date: datetime
    updated_date: Union[datetime, None]

class OpenPeriodPayroll(BaseModel):
    period: str = None

class ClosePeriodPayroll(BaseModel):
    period: str = None

class EndDocument(BaseModel):
    causal_id: int = None
    document_type_id: int = None
    status_id:int  = None
    rut: str  = None
    fertility_proportional_days: str = None
    voluntary_indemnity: int = None
    indemnity_years_service: int = None
    substitute_compensation: int = None
    fertility_proportional: int = None
    total: int = None
    
class UpdateDocumentType(BaseModel):
    document_type: str = None
    document_group_id: int = None
    order: int = None
    updated_date: Union[datetime, None]

class FamilyType(BaseModel):
    id: int
    family_type: str
    added_date: str
    updated_date: str

class UpdateFamilyType(BaseModel):
    family_type: str
    updated_date: str = None

class KardexDatum(BaseModel):
    status_id: int
    document_type_id: int
    old_document_status_id: int
    rut: int

    @classmethod
    def as_form(cls, 
                status_id: int = Form(),
                document_type_id: int = Form(),
                old_document_status_id: int = Form(),
                rut: int = Form()
                ):
        return cls(status_id=status_id, document_type_id=document_type_id, old_document_status_id=old_document_status_id, rut=rut)
   
class FamilyCoreDatum(BaseModel):
    family_type_id: int
    employee_rut: int
    gender_id: int
    rut: str
    names: str
    father_lastname: str
    mother_lastname: str
    born_date: str

    @classmethod
    def as_form(cls, 
                family_type_id: int = Form(),
                employee_rut: int = Form(),
                gender_id: int = Form(),
                rut: str = Form(),
                names: str = Form(),
                father_lastname: str = Form(),
                mother_lastname: str = Form(),
                born_date: str = Form()
                ):
        return cls(family_type_id=family_type_id, employee_rut=employee_rut, gender_id=gender_id, rut=rut, names=names, father_lastname=father_lastname, mother_lastname=mother_lastname, born_date=born_date)
   
class OldFamilyCoreDatum(BaseModel):
    family_type_id: int
    employee_rut: int
    gender_id: int
    rut: str
    names: str
    father_lastname: str
    mother_lastname: str
    born_date: str

class DteAtmMachine(BaseModel):
    branch_office_id: int
    cashier_id: int
    dte_type_id: int
    sii_send_status_id: str
    sii_status_id: str
    sii_track_id: str
    dte_code: str
    folio: str
    cash_amount: int
    card_amount: int
    subtotal:int
    tax: int
    discount: int
    total: int
    ticket_serial_number: int
    ticket_hour: str
    ticket_transaction_number: int
    ticket_dispenser_number: int
    ticket_number: int
    ticket_station_number: int
    ticket_sa: str
    ticket_correlative: int
    entrance_hour: str
    exit_hour: str
    item_quantity: int
    sii_date: str
    added_date: str

class ProvisionalIndicator(BaseModel):
    period: str
    month_value_1: str
    month_value_2: str
    month_value_3: str
    uf_value_current_month: str
    uf_value_last_month: str
    utm_value_current_month: str
    uta_value_current_month: str
    cap_income_tax_afp: str
    cap_income_tax_ips: str
    cap_income_tax_unemployment: str
    minimun_income_tax_dependent_independet: str
    minimun_income_tax_under_18_over_65: str
    minimun_income_tax_domestic_worker: str
    minimun_income_tax_non_remunerational: str
    voluntary_pension_savings_monthly: str
    voluntary_pension_savings_annual: str
    agreed_deposit_annual: str
    indefinite_term_worker: str
    fixed_term_worker: str
    indefinite_term_worker_11_years: str
    domestic_worker: str
    indefinite_term_employeer: str
    fixed_term_employeer: str
    indefinite_term_employeer_11_years: str
    domestic_employeer: str
    capital_dependent_rate_afp: str
    capital_dependent_sis: str
    capital_independent_rate_afp: str
    cuprum_dependent_rate_afp: str
    cuprum_dependent_sis: str
    cuprum_independent_rate_afp: str
    habitat_dependent_rate_afp: str
    habitat_dependent_sis: str
    habitat_independent_rate_afp: str
    planvital_dependent_rate_afp: str
    planvital_dependent_sis: str
    planvital_independent_rate_afp: str
    provida_dependent_rate_afp: str
    provida_dependent_sis: str
    provida_independent_rate_afp: str
    modelo_dependent_rate_afp: str
    modelo_dependent_sis: str
    modelo_independent_rate_afp: str
    uno_dependent_rate_afp: str
    uno_dependent_sis_input: str
    uno_independent_rate_afp: str
    a_family_assignment_amount: str
    a_family_assignment_rent_requirement_input_minimum_value: str
    a_family_assignment_rent_requirement_input_top_value: str
    b_family_assignment_amount: str
    b_family_assignment_rent_requirement_input_minimum_value: str
    b_family_assignment_rent_requirement_input_top_value: str
    c_family_assignment_amount: str
    c_family_assignment_rent_requirement_input_minimum_value: str
    c_family_assignment_rent_requirement_input_top_value: str
    d_family_assignment_amount: str
    d_family_assignment_rent_requirement_input_minimum_value: str
    d_family_assignment_rent_requirement_input_top_value: str
    hard_work_porcentage: str
    hard_work_employeer: str
    hard_work_worker: str
    less_hard_work_porcentage: str
    less_hard_work_employeer: str
    less_hard_work_worker: str
    distribution_7_percent_health_employeer_ccaf: str
    distribution_7_percent_health_employeer_fonasa: str
    mutual_value: str
    honorary_value: str
    gratification_value: str

class UpdateFamilyCoreDatum(BaseModel):
    family_type_id: int = None
    employee_rut: int = None
    gender_id: int = None
    rut: str = None
    names: str = None
    father_lastname: str = None
    mother_lastname: str = None
    born_date: str = None

    @classmethod
    def as_form(cls, 
                family_type_id: int = Form(),
                employee_rut: int = Form(),
                gender_id: int = Form(),
                rut: str = Form(),
                names: str = Form(),
                father_lastname: str = Form(),
                mother_lastname: str = Form(),
                born_date: str = Form()
                ):
        return cls(family_type_id=family_type_id, employee_rut=employee_rut, gender_id=gender_id, rut=rut, names=names, father_lastname=father_lastname, mother_lastname=mother_lastname, born_date=born_date)
   
class Vacation(BaseModel):
    rut: int
    since: str
    until: str
    no_valid_days: int
    status_id: int
    document_type_id: int

class ProgressiveVacation(BaseModel):
    rut: int
    since: str
    until: str
    no_valid_days: int
    status_id: int
    document_type_id: int

class UpdateVacation(BaseModel):
    document_employee_id: int = None
    rut: int = None
    since: str = None
    until: str = None
    days: int = None
    no_valid_days: int = None
    support: UploadFile = None
    updated_date: str = Union[datetime, None]

class MedicalLicense(BaseModel):
    medical_license_type_id: int
    patology_type_id: int
    document_type_id: int
    rut: int
    folio: str
    since: str
    until: str
    status_id: int

    @classmethod
    def as_form(cls, 
                medical_license_type_id: int = Form(),
                patology_type_id: int = Form(),
                document_type_id: int = Form(),
                rut: int = Form(),
                folio: str = Form(),
                since: str = Form(),
                until: str = Form(),
                status_id: int = Form()
                ):
        return cls(medical_license_type_id=medical_license_type_id,document_type_id=document_type_id,patology_type_id=patology_type_id, rut=rut, folio=folio, since=since, until=until, status_id=status_id)

class SalarySettlement(BaseModel):
    status_id: int
    document_type_id: int
    rut: int

    @classmethod
    def as_form(cls, 
                status_id: int = Form(),
                document_type_id: int = Form(),
                rut: int = Form(),
                ):
        return cls(status_id=status_id,document_type_id=document_type_id,rut=rut)

class UpdateMedicalLicense(BaseModel):
    document_employee_id: int = None
    medical_license_type_id: int = None
    patology_type_id: int = None
    period: str = None
    rut: int = None
    folio: int = None
    since: str = None
    until: str = None
    days: int = None
    updated_date: Union[datetime, None]

class Rol(BaseModel):
    rol: str
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateRol(BaseModel):
    rol: str = None
    updated_date: Union[datetime, None]

class HealthModel(BaseModel):
    id: int
    health_remuneration_code: int
    health: str
    rut: int
    previred_code: int
    added_date: str
    updated_date: str

class UpdateHealthModel(BaseModel):
    health_remuneration_code: int = None
    health: str = None
    rut: int = None
    previred_code: int = None
    updated_date: Union [datetime, None]

class New(BaseModel):
    title: str
    description: str
    markdown_description: str
    picture: UploadFile
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateNew(BaseModel):
    title: str = None
    description: str = None
    markdown_description: str = None
    picture: str = None
    updated_date: str = None

class Principal(BaseModel):
    principal: str
    added_date: datetime
    updated_date: Union[datetime, None]

class Zone(BaseModel):
    zone: str
    added_date: datetime
    updated_date: Union[datetime, None]
    

class UpdatePrincipal(BaseModel):
    principal: str = None
    updated_date: Union[datetime, None]

class UpdateZone(BaseModel):
    zone: str = None
    updated_date: Union[datetime, None]

class Commune(BaseModel):
    region_id: int
    commune: str
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateCommune(BaseModel):
    region_id: int = None
    commune: str = None
    updated_date: Union[datetime, None]

class Health(BaseModel):
    health_remuneration_code: int
    health: str
    rut: int
    previred_code: int
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateHealth(BaseModel):
    health_remuneration_code: int = None
    health: str = None
    rut: int = None
    previred_code: int = None
    updated_date: Union[datetime, None]

class EmployeeBankAccount(BaseModel):
    rut: int
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateEmployeeBankAccount(BaseModel):
    bank_id: int = None
    account_type_id: int = None
    rut: int = None
    account_number: str = None

class StoreEmployeeBankAccount(BaseModel):
    bank_id: int = None
    account_type_id: int = None
    rut: int = None
    account_number: str = None

class DocumentEmployee(BaseModel):
    status_id: int
    document_type_id: int
    rut: int

class OldDocumentEmployee(BaseModel):
    status_id: int
    rut: int
    document_type_id: int
    support: str
    
class DocumentManagement(BaseModel):
    status_id: int
    document_type_id: int
    rut: int

class UpdateDocumentEmployee(BaseModel):
    status_id: int = None
    document_type_id: int = None
    old_document_status_id: int = None
    rut: int = None
    since: str = None
    until: str = None
    no_valid_days: int = None
    support: str = None

class UploadDocumentEmployee(BaseModel):
    id: int
    rut: int
    file_name: str
    dropbox_path: str
    support: UploadFile
    updated_date: str = None

class PayrollEmployeeInput(BaseModel):
    rut: int
    payroll_item_id: int
    amount: Union[str, None]
    period: str

class VerifyComplaint(BaseModel):
    id: str = None
    password: str = None

class Complaint(BaseModel):
    relationship: str = None
    incident_place: str = None
    complaint_type: str = None
    anonymous: str = None
    incident_date: str = None
    incident_place_detail: str = None
    knowledge: str = None
    identify: str = None
    description: str = None
    password: str = None
    email: str = None

    @classmethod
    def as_form(cls,
                relationship: str = Form(None),
                incident_place: str = Form(None),
                complaint_type: str = Form(None),
                anonymous: str = Form(None),
                incident_date: str = Form(None),
                incident_place_detail: str = Form(None),
                knowledge: str = Form(None),
                identify: str = Form(None),
                description: str = Form(None),
                password: str = Form(None),
                email: str = Form(None)):
        return cls(relationship=relationship, incident_place=incident_place, complaint_type=complaint_type, anonymous=anonymous, incident_date=incident_date, incident_place_detail=incident_place_detail, knowledge=knowledge, identify=identify, description=description, password=password, email=email)

class PayrollDataInput(BaseModel):
    payroll_employees: List[PayrollEmployeeInput]

class UpdatePayrollItemValue(BaseModel):
    rut: int
    item_id: int
    amount: int
    period: str

class UpdatePayrollItemDataValue(BaseModel):
    payroll_item_values: List[UpdatePayrollItemValue]

class UploadFamilyBurden(BaseModel):
    rut: str
    period: str

    @classmethod
    def as_form(cls, 
                rut: str = Form(),
                period: str = Form(),
                ):
        return cls(rut=rut, period=period)

class UploadPayrollManualInput(BaseModel):
    rut: str
    payroll_item_id: int
    period: str
    amount: int

    @classmethod
    def as_form(cls, 
                rut: str = Form(),
                payroll_item_id: int = Form(),
                period: str = Form(),
                amount: int = Form()
                ):
        return cls(rut=rut, payroll_item_id=payroll_item_id, period=period, amount=amount)
    
class SearchEmployee(BaseModel):
    rut: Union[str, None]
    names: Union[str, None]
    father_lastname: Union[str, None]
    mother_lastname: Union[str, None]
    status_id: int = None
    branch_office_id: str = None
    user_rut: str
    rol_id: int
    page: int

class SearchDeposit(BaseModel):
    branch_office_id: Union[int, None]
    status_id: Union[int, None]
    since: Union[str, None]
    until: Union[str, None]

class SearchPayrollEmployee(BaseModel):
    rut: Union[str, None]
    father_lastname: Union[str, None]

class ClockUser(BaseModel):
    rut: str
    names: str
    father_lastname: str
    mother_lastname: str
    privilege: str
    added_date: Union[str, None]
    updated_date: Union[str, None]

class UpdateClockUser(BaseModel):
    rut: str = None
    names: str = None
    father_lastname: str = None
    privilege: str = None

class ContractDatum(BaseModel):
    rut: int
    status_id: int
    document_type_id: int

class IndemnityYear(BaseModel):
    rut: int
    exit_company: str

class SubstituteCompensation(BaseModel):
    rut: int

class FertilityProportional(BaseModel):
    rut: int 
    exit_company: str
    balance: float
    number_holidays:int

class ContractType(BaseModel):
    contract_type: str
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateContractType(BaseModel):
    contract_type: str = None
    updated_date: Union[datetime, None]

class MedicalLicenseType(BaseModel):
    medical_license_type: str
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateMedicalLicenseType(BaseModel):
    medical_license_type: str = None
    updated_date: Union[datetime, None]

class GetBudget(BaseModel):
    rut: str = None
    rol_id: int = None
    api_token: str = None

class GetCollection(BaseModel):
    rut: str = None
    rol_id: int = None
    api_token: str = None

class GetDte(BaseModel):
    rut: str = None
    rol_id: int = None
    api_token: str = None

class LetterType(BaseModel):
    letter_type: str
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateLetterType(BaseModel):
    letter_type: str = None
    updated_date: Union[datetime, None]

class UploadContract(BaseModel):
    id: int
    support: UploadFile
    rut: int
    updated_date: Union[datetime, None]

class SelectDocumentEmployee(BaseModel):
    rut: int

class DownloadDocumentEmployee(BaseModel):
    id: int

class UploadVacation(BaseModel):
    vacation_id: int
    rut: int

    @classmethod
    def as_form(cls, 
                vacation_id: int = Form(),
                rut: int = Form()
                ):
        return cls(vacation_id=vacation_id, rut=rut)

class UploadEmployeeContract(BaseModel):
    id: int
    rut: int

    @classmethod
    def as_form(cls, 
                id: int = Form(),
                rut: int = Form()
                ):
        return cls(id=id, rut=rut)
    
class UploadSignature(BaseModel):
    rut: int
    signature: str
    signature_type_id: int

    @classmethod
    def as_form(cls,
                    rut: int = Form(),
                    signature: str = Form(),
                    signature_type_id: int = Form()
                ):
        return cls(rut=rut, signature=signature, signature_type_id=signature_type_id)

class UploadPicture(BaseModel):
    rut: int

    @classmethod
    def as_form(cls,
                    rut: int = Form()
                ):
        return cls(rut=rut)


class UpdateAboutUs(BaseModel):
    text: str
class UpdateContact(BaseModel):
    address: str
    cellphone: str
    email: str

# Clase para representar los datos del formulario
class PossibleEmployeeFormData(BaseModel):
    names: str
    region: int
    commune: int

    @classmethod
    def as_form(cls, 
                names: str = Form(),
                region: int = Form(),
                commune: int = Form()):
        return cls(names=names, region=region, commune=commune)

class CreatePossibleEmployee(BaseModel):
    names: str
    region: int
    commune: int
    @classmethod
    def as_form(cls, 
                names: str = Form(),
                region: int = Form(),
                commune: int = Form()                ):
        return cls(names=names, region=region, commune=commune)
    
class CreateBlog(BaseModel):
    title: str
    description: str

    @classmethod
    def as_form(cls, 
                title: str = Form(),
                description: str = Form(),
                
                ):
        return cls(title=title, description=description)

class Day(BaseModel):
    id: Optional[int] = None
    group_day_id: Optional[int] = None
    visibility_id: Optional[int] = None
    free_day_group_id: Optional[int] = None
    group_id: Optional[int] = None
    employee_type_id: Optional[int] = None
    breaking: Optional[str] = None
    day_hours: Optional[int] = None
    end: Optional[str] = None
    end_collation_time_threshold: Optional[str] = None
    end_entry_time_threshold: Optional[str] = None
    end_exit_time_threshold: Optional[str] = None
    start: Optional[str] = None
    start_collation_time_threshold: Optional[str] = None
    start_entry_time_threshold: Optional[str] = None
    start_exit_time_threshold: Optional[str] = None
    total_week_hours: Optional[int] = None
    turn: Optional[str] = None
    working: Optional[str] = None
    added_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None

class CreateSchedule(BaseModel):
    schedule: Optional[Dict[str, Day]]
    horary_name: Optional[str] = None
    added_date: datetime
    updated_date: Union[datetime, None]

class CreateFrecuentQuestion(BaseModel):
    question: str
    answer: str

class UploadProgressiveVacation(BaseModel):
    progressive_vacation_id: int
    rut: int

    @classmethod
    def as_form(cls, 
                progressive_vacation_id: int = Form(),
                rut: int = Form()
                ):
        return cls(progressive_vacation_id=progressive_vacation_id, rut=rut)

class UploadMedicalLicense(BaseModel):
    medical_license_id: int
    rut: int

    @classmethod
    def as_form(cls, 
                medical_license_id: int = Form(),
                rut: int = Form()
                ):
        return cls(medical_license_id=medical_license_id, rut=rut)
    
class MeshDatum(BaseModel):
    turn_id: int
    rut: int
    date: str
    total_hour: str
    start: str
    end: str
    week: int
    week_day: int
    status_id: int
    document_type_id: int
    period: str
    added_date: datetime
    updated_date: Union[datetime, None]

class Mesh(BaseModel):
    week_id: int
    turn_id: int
    rut: int
    date: str
    added_date: datetime

class MeshList(BaseModel):
    meshes: List[Mesh]

class LoginTest(BaseModel):
    username: str
    password: str

class ForgotPassword(BaseModel):
    rut: str
    email: str

class UpdatePassWord(BaseModel):
    visual_rut: str = None
    hashed_password: str = None
    updated_date: Union[datetime, None]
class ConfirmEmail(BaseModel):
    visual_rut: str = None
    personal_email: str = None
    updated_date: Union[datetime, None]

class EmployeeList(BaseModel):
    rut: int
    rol_id: int
    page: int

class PayrollItemList(BaseModel):
    page: int

class AlertList(BaseModel):
    rut: int
    page: int

class HonoraryList(BaseModel):
    rut: int
    rol_id: int
    page: int