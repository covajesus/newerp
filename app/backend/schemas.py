from pydantic import BaseModel, Field, EmailStr
from fastapi import UploadFile, File
from typing import Union, List, Dict, Optional
from datetime import datetime
from decimal import Decimal
from fastapi import Form
from typing import List
from typing import Optional

class Alert(BaseModel):
    alert_type_id: int
    status_id: int
    rut: int

class UpdateAlert(BaseModel):
    status_id: int = None

class CreateBranchOffice(BaseModel):
    branch_office: str
    dte_code: str
    address: str
    region_id: int
    commune_id: int
    segment_id: int
    basement_id: int
    zone_id: int
    principal_id: int
    status_id: int
    visibility_id: int
    getaway_machine_id: int
    opening_date: str
    principal_supervisor: str

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

class UploadDteDepositTransfer(BaseModel):
    dte_id: int
    payment_type_id: int
    payment_number: str
    deposited_amount: int
    deposit_date: str

    @classmethod
    def as_form(cls,
                dte_id: int = Form(...),
                payment_type_id: int = Form(...),
                payment_number: str = Form(...),
                deposited_amount: int = Form(...),
                deposit_date: str = Form(...)
            ):
        return cls(
            dte_id=dte_id,
            payment_type_id=payment_type_id,
            payment_number=payment_number,
            deposited_amount=deposited_amount,
            deposit_date=deposit_date
        )
        
class UpdateBranchOffice(BaseModel):
    id: int
    branch_office: str = None
    address: str = None
    region_id: int = None
    commune_id: int = None
    segment_id: int = None
    zone_id: str = None
    principal_id: int = None
    basement_id: int = None
    status_id: int = None
    visibility_id: int = None
    dte_code: str = None
    opening_date: Union[str, None]
    closing_date: Union[str, None]
    principal_supervisor: str = None
    getaway_machine_id: int = None

    @classmethod
    def as_form(cls,
        id: int = Form(None),
        branch_office: str = Form(None),
        address: str = Form(None),
        region_id: int = Form(None),
        commune_id: int = Form(None),
        segment_id: int = Form(None),
        zone_id: str = Form(None),
        principal_id: int = Form(None),
        basement_id: int = Form(None),
        status_id: int = Form(None),
        visibility_id: int = Form(None),
        dte_code: str = Form(None),
        opening_date: str = Form(None),
        closing_date: str = Form(None),
        principal_supervisor: str = Form(None),
        getaway_machine_id: int = Form(None)
    ):
        return cls(
            id=id,
            branch_office=branch_office,
            address=address,
            region_id=region_id,
            commune_id=commune_id,
            segment_id=segment_id,
            zone_id=zone_id,
            principal_id=principal_id,
            basement_id=basement_id,
            status_id=status_id,
            visibility_id=visibility_id,
            dte_code=dte_code,
            opening_date=opening_date,
            closing_date=closing_date,
            principal_supervisor=principal_supervisor,
            getaway_machine_id=getaway_machine_id
        )
    
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
    rut: Union[int, None]
    branch_office_id: Union[int, None]
    full_name: Union[str, None]
    email: Union[str, None]
    phone: Union[str, None]
    hashed_password: Union[str, None]

class RecoverUser(BaseModel):
    rut: str
    email: str

class User(BaseModel):
    rol_id: int
    branch_office_id: Union[int, None]
    rut: str
    full_name: str
    email: str
    password: str
    phone: str

class UpdateUser(BaseModel):
    rol_id: int = None
    rut: str = None
    full_name: str = None
    email: str = None
    phone: str = None

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
    honorary_reason_id: int
    branch_office_id: int
    foreigner_id: int
    bank_id: int
    schedule_id: int
    region_id: int
    commune_id: int
    employee_to_replace: str
    replacement_employee_rut: Union[str, None]
    replacement_employee_full_name: str
    address: str
    account_type_id: int
    account_number: str
    start_date: Union[str, None]
    end_date: Union[str, None]
    observation: str
    amount: int
    observation: str

    @classmethod
    def as_form(cls,
                honorary_reason_id: int = Form(),
                branch_office_id: int = Form(),
                foreigner_id: int = Form(),
                bank_id: int = Form(),
                schedule_id: int = Form(),
                region_id: int = Form(),
                commune_id: int = Form(),
                employee_to_replace: str = Form(),
                replacement_employee_rut: str = Form(None),
                replacement_employee_full_name: str = Form(),
                address: str = Form(),
                account_type_id: int = Form(),
                account_number: str = Form(),
                start_date: str = Form(None),
                end_date: str = Form(None),
                amount: int = Form(),
                observation: str = Form()
                ):
        
        return cls(honorary_reason_id=honorary_reason_id, account_type_id=account_type_id, branch_office_id=branch_office_id, foreigner_id=foreigner_id, bank_id=bank_id, schedule_id=schedule_id, region_id=region_id, commune_id=commune_id, employee_to_replace=employee_to_replace, replacement_employee_rut=replacement_employee_rut, replacement_employee_full_name=replacement_employee_full_name, address=address, account_number=account_number, start_date=start_date, end_date=end_date, amount=amount, observation=observation)

class ValidateHonoraryRut(BaseModel):
    replacement_employee_rut: str
    added_date: str

    @classmethod
    def as_form(cls, 
                replacement_employee_rut: str = Form(),
                added_date: str = Form()
                ):
        return cls(replacement_employee_rut=replacement_employee_rut, added_date=added_date)
   
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
    account_type_id: int = None
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

class Dte(BaseModel):
    branch_office_id: int
    cashier_id: int
    dte_type_id: int
    folio: int
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


class Rol(BaseModel):
    rol: str
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateRol(BaseModel):
    rol: str = None
    updated_date: Union[datetime, None]

class Tax(BaseModel):
    period: str

    @classmethod
    def as_form(cls, 
                period: str = Form()
                ):
        return cls(period=period)

class Deposit(BaseModel):
    branch_office_id: int
    total: int
    collection_date: str
    collection_id: int
    collection_amount: int
    payment_type_id: int
    deposited_amount: int
    deposit_date: str
    payment_number: str

    @classmethod
    def as_form(cls,
                branch_office_id: int = Form(),
                total: int = Form(),
                collection_id: int = Form(),
                collection_amount: int = Form(),
                collection_date: str = Form(),
                payment_type_id: int = Form(),
                deposited_amount: int = Form(),
                deposit_date: str = Form(),
                payment_number: str = Form()
                ):
        return cls(branch_office_id=branch_office_id, total=total, collection_amount=collection_amount, collection_id=collection_id, collection_date=collection_date, payment_type_id=payment_type_id, deposited_amount=deposited_amount, deposit_date=deposit_date, payment_number=payment_number)

class Patent(BaseModel):
    branch_office_id: int
    semester: str
    year: int

    @classmethod
    def as_form(cls, 
                branch_office_id: int = Form(),
                semester: str = Form(),
                year: int = Form(),
                ):
        return cls(branch_office_id=branch_office_id, semester=semester, year=year)

class UpdateCapitulation(BaseModel):
    id: int
    question: str
    why_was_rejected: str = None

    @classmethod
    def as_form(cls,
                id: int = Form(),
                question: str = Form(),
                why_was_rejected: str = Form(None)
                ):
        return cls(id=id, question=question, why_was_rejected=why_was_rejected)

class PayCapitulation(BaseModel):
    payment_date: str
    payment_number: str
    selected_capitulations: List[int]

    @classmethod
    def as_form(cls,
                payment_date: str = Form(),
                payment_number: str = Form(),
                selected_capitulations: List[int] = Form(...),
                ):
        return cls(payment_date=payment_date, payment_number=payment_number, selected_capitulations=selected_capitulations)

class ImputeHonorary(BaseModel):
    id: int
    period: str
    expense_type_id: int

    @classmethod
    def as_form(cls,
                id: int = Form(),
                period: str = Form(),
                expense_type_id: int = Form()
                ):
        return cls(id=id, period=period, expense_type_id=expense_type_id)

class UpdateSetting(BaseModel):
    capitulation_open_period: str
    capitulation_close_period: str
    honorary_open_period: str
    honorary_close_period: str
    dropbox_token: str
    facebook_token: str
    simplefactura_token: str
    caf_limit: str
    percentage_honorary_bill: str
    apigetaway_token: str

    @classmethod
    def as_form(cls,
                capitulation_open_period: str = Form(),
                capitulation_close_period: str = Form(),
                honorary_open_period: str = Form(),
                honorary_close_period: str = Form(),
                dropbox_token: str = Form(),
                facebook_token: str = Form(),
                simplefactura_token: str = Form(),
                caf_limit: str = Form(),
                percentage_honorary_bill: str = Form(),
                apigetaway_token: str = Form()
                ):
        return cls(capitulation_open_period=capitulation_open_period, capitulation_close_period=capitulation_close_period, honorary_open_period=honorary_open_period, honorary_close_period=honorary_close_period, dropbox_token=dropbox_token, facebook_token=facebook_token, simplefactura_token=simplefactura_token, caf_limit=caf_limit, percentage_honorary_bill=percentage_honorary_bill, apigetaway_token=apigetaway_token)
    
class ImputeCapitulation(BaseModel):
    id: int
    period: str

    @classmethod
    def as_form(cls,
                id: int = Form(),
                period: str = Form()
                ):
        return cls(id=id, period=period)
    
class Capitulation(BaseModel):
    document_date: str
    supplier_rut: str
    document_number: str
    document_type_id: int
    capitulation_type_id: int
    branch_office_id: int
    expense_type_id: int
    description: str
    amount: int

    @classmethod
    def as_form(cls,
                document_date: str = Form(),
                supplier_rut: str = Form(),
                document_number: str = Form(),
                document_type_id: int = Form(),
                capitulation_type_id: int = Form(),
                branch_office_id: int = Form(),
                expense_type_id: int = Form(),
                description: str = Form(),
                amount: int = Form()
                ):
        return cls(document_date=document_date, supplier_rut=supplier_rut, document_number=document_number, document_type_id=document_type_id, capitulation_type_id=capitulation_type_id, branch_office_id=branch_office_id, expense_type_id=expense_type_id, description=description, amount=amount)
    
class CarbonMonoxide(BaseModel):
    branch_office_id: int
    measure_value: str
    added_date: str

    @classmethod
    def as_form(cls, 
                branch_office_id: int = Form(),
                measure_value: str = Form(),
                added_date: str = Form(),
                ):
        return cls(branch_office_id=branch_office_id, measure_value=measure_value, added_date=added_date)

class SinisterReview(BaseModel):
    sinister_id: int
    sinister_step_type_id: int
    sinister_version_id: int
    review_description: Optional[str] = None
    answer_step_1: Optional[int] = None

    @classmethod
    def as_form(cls,
                sinister_id: int = Form(),
                sinister_step_type_id: int = Form(),
                sinister_version_id: int = Form(),
                review_description: str = Form(None),
                answer_step_1: int = Form(None)
                ):
        return cls(sinister_id=sinister_id, sinister_step_type_id=sinister_step_type_id, sinister_version_id=sinister_version_id, review_description=review_description, answer_step_1=answer_step_1)

class DepositIds(BaseModel):
    deposit_ids: List[int]
    
class Sinister(BaseModel):
    branch_office_id: int
    sinister_type_id: int
    protected_area_id: Optional[int] = None
    registered_event_id: Optional[int] = None
    notified_security_id: Optional[int] = None
    denounced_authorities_id: Optional[int] = None
    sinister_date: str
    client_name: str
    client_last_name: str
    client_rut: str
    client_phone: str
    client_email: str
    brand: Optional[str] = None
    model: Optional[str] = None
    patent: Optional[str] = None
    year: Optional[str] = None
    color: Optional[str] = None
    description: str

    @classmethod
    def as_form(cls,
                branch_office_id: int = Form(),
                sinister_type_id: int = Form(),
                protected_area_id: int = Form(None),
                registered_event_id: int = Form(None),
                notified_security_id: int = Form(None),
                denounced_authorities_id: int = Form(None),
                sinister_date: str = Form(),
                client_name: str = Form(),
                client_last_name: str = Form(),
                client_rut: str = Form(),
                client_phone: str = Form(),
                client_email: str = Form(),
                brand: Optional[str] = Form(None),
                model: Optional[str] = Form(None),
                patent: Optional[str] = Form(None),
                year: Optional[str] = Form(None),
                color: Optional[str] = Form(None),
                description: str = Form()
                ):
        return cls(branch_office_id=branch_office_id, sinister_type_id=sinister_type_id, protected_area_id=protected_area_id, registered_event_id=registered_event_id, notified_security_id=notified_security_id, denounced_authorities_id=denounced_authorities_id, sinister_date=sinister_date, client_name=client_name, client_last_name=client_last_name, client_rut=client_rut, client_phone=client_phone, client_email=client_email, brand=brand, model=model, patent=patent, year=year, color=color, description=description)

class BankStatement(BaseModel):
    period: str

    @classmethod
    def as_form(cls, 
                period: str = Form()
            ):
        return cls(period=period)

class StoreAccountability(BaseModel):
    period: str

    @classmethod
    def as_form(cls, 
                period: str = Form()
            ):
        return cls(period=period)
    
class TransbankStatement(BaseModel):
    period: str

    @classmethod
    def as_form(cls, 
                period: str = Form()
            ):
        return cls(period=period)
    
class Contract(BaseModel):
    rut: str
    client: str
    start_date: str
    renovation_date: str
    end_date: str
    branch_office_id: int
    address: str
    contract_type_id: int
    currency: str
    amount: int

    @classmethod
    def as_form(cls, 
                rut: str = Form(),
                client: str = Form(),
                start_date: str = Form(),
                renovation_date: str = Form(),
                branch_office_id: int = Form(),
                address: str = Form(),
                contract_type_id: int = Form(),
                end_date: str = Form(),
                currency: str = Form(),
                amount: int = Form()
            ):
        return cls(rut=rut, client=client, start_date=start_date, end_date=end_date, currency=currency, amount=amount, renovation_date=renovation_date, branch_office_id=branch_office_id, address=address, contract_type_id=contract_type_id)

class Customer(BaseModel):
    rut: str
    region_id: int
    commune_id: int
    customer: str
    email: str
    phone: str
    activity: str
    address: str

class ReportRequest(BaseModel):
    selected_carbon_monoxides: list[dict]
    email: EmailStr

from fastapi import Form
from pydantic import BaseModel

class CashReserve(BaseModel):
    branch_office_id: int
    cashier_id: int
    amount: int

    @classmethod
    def as_form(
        cls,
        branch_office_id: int = Form(...),
        cashier_id: int = Form(...),
        amount: int = Form(...)
    ):
        return cls(
            branch_office_id=branch_office_id,
            cashier_id=cashier_id,
            amount=amount
        )

from fastapi import Form, UploadFile
from pydantic import BaseModel
from typing import Optional

class Demarcation(BaseModel):
    branch_office_id: int
    material_costs: str
    labor_costs: str
    made_arrows: int
    made_pedestrian_crossing: int
    made_disability: int
    made_island: int
    made_pregnant: int
    made_wall: int

    file_made_arrows: Optional[UploadFile] = None
    file_made_pedestrian_crossing: Optional[UploadFile] = None
    file_made_disability: Optional[UploadFile] = None
    file_made_island: Optional[UploadFile] = None
    file_made_pregnant: Optional[UploadFile] = None
    file_made_wall: Optional[UploadFile] = None

    @classmethod
    def as_form(
        cls,
        branch_office_id: int = Form(...),
        material_costs: str = Form(...),
        labor_costs: str = Form(...),
        made_arrows: int = Form(...),
        made_pedestrian_crossing: int = Form(...),
        made_disability: int = Form(...),
        made_island: int = Form(...),
        made_pregnant: int = Form(...),
        made_wall: int = Form(...),
        file_made_arrows: Optional[UploadFile] = None,
        file_made_pedestrian_crossing: Optional[UploadFile] = None,
        file_made_disability: Optional[UploadFile] = None,
        file_made_island: Optional[UploadFile] = None,
        file_made_pregnant: Optional[UploadFile] = None,
        file_made_wall: Optional[UploadFile] = None
    ):
        return cls(
            branch_office_id=branch_office_id,
            material_costs=material_costs,
            labor_costs=labor_costs,
            made_arrows=made_arrows,
            made_pedestrian_crossing=made_pedestrian_crossing,
            made_disability=made_disability,
            made_island=made_island,
            made_pregnant=made_pregnant,
            made_wall=made_wall,
            file_made_arrows=file_made_arrows,
            file_made_pedestrian_crossing=file_made_pedestrian_crossing,
            file_made_disability=file_made_disability,
            file_made_island=file_made_island,
            file_made_pregnant=file_made_pregnant,
            file_made_wall=file_made_wall,
        )

class CashReserveList(BaseModel):
    branch_office_id: Optional[int] = None
    page: int = 0

class TransbankStatementList(BaseModel):
    page: int = 0

class DemarcationList(BaseModel):
    page: int = 0

class CarbonMonoxideList(BaseModel):
    branch_office_id: Optional[int] = None
    since_date: Optional[str] = None
    until_date: Optional[str] = None
    page: int = 0

class SinisterList(BaseModel):
    branch_office_id: Optional[int] = None
    page: int = 0

class DteList(BaseModel):
    folio: Optional[str] = None  # Opcional con valor predeterminado None
    branch_office_id: Optional[int] = None  # Opcional con valor predeterminado None
    rut: Optional[str] = None  # Opcional con valor predeterminado None
    customer: Optional[str] = None  # Opcional con valor predeterminado None
    period: Optional[str] = None  # Opcional con valor predeterminado None
    amount: Optional[str] = None  # Opcional con valor predeterminado None
    supervisor_id: Optional[str] = None  # Opcional con valor predeterminado None
    status_id: Optional[int] = None  # Opcional con valor predeterminado None
    dte_version_id: Optional[int] = None  # Opcional con valor predeterminado None
    page: int = 0  # Opcional con valor predeterminado 0

class ReceivedDteList(BaseModel):
    folio: Optional[str] = None  # Opcional con valor predeterminado None
    branch_office_id: Optional[int] = None  # Opcional con valor predeterminado None
    rut: Optional[str] = None  # Opcional con valor predeterminado None
    supplier: Optional[str] = None  # Opcional con valor predeterminado None
    since: Optional[str] = None  # Opcional con valor predeterminado None
    until: Optional[str] = None  # Opcional con valor predeterminado None
    amount: Optional[str] = None  # Opcional con valor predeterminado None
    supervisor_id: Optional[str] = None  # Opcional con valor predeterminado None
    status_id: Optional[int] = None  # Opcional con valor predeterminado None
    dte_version_id: Optional[int] = None  # Opcional con valor predeterminado None
    dte_type_id: Optional[int] = None  # Opcional con valor predeterminado None
    page: int = 0  # Opcional con valor predeterminado 0

class ImportDte(BaseModel):
    rut: str

class CustomerList(BaseModel):
    rut: Optional[str] = None  # Opcional con valor predeterminado None
    page: int = 0  # Opcional con valor predeterminado 0

class CollectionList(BaseModel):
    branch_office_id: Optional[int] = None  # Opcional con valor predeterminado None
    cashier_id: Optional[int] = None  # Opcional con valor predeterminado None
    added_date: Optional[str] = None  # Opcional con valor predeterminado None
    page: int = 0  # Opcional con valor predeterminado 0

class UpdateCustomer(BaseModel):
    rut: str
    region_id: int
    commune_id: int
    customer: str
    phone: str
    email: str
    activity: str
    address: str

class Commune(BaseModel):
    region_id: int
    commune: str
    added_date: datetime
    updated_date: Union[datetime, None]

class UpdateCommune(BaseModel):
    region_id: int = None
    commune: str = None
    updated_date: Union[datetime, None]

class PayrollEmployeeInput(BaseModel):
    rut: int
    payroll_item_id: int
    amount: Union[str, None]
    period: str

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

class ContractList(BaseModel):
    rut: Optional[str] = None  # Ahora es opcional
    branch_office_id: Optional[int] = None  # Ahora es opcional
    page: int

class TaxList(BaseModel):
    period: Optional[str] = None  # Ahora es opcional
    page: int

class PatentList(BaseModel):
    branch_office_id: Optional[int] = None  # Ahora es opcional
    semester: Optional[str] = None  # Ahora es opcional
    year: Optional[int] = None  # Ahora es opcional
    page: int

class CapitulationList(BaseModel):
    page: int

class CashierList(BaseModel):
    page: int

class IntershipList(BaseModel):
    branch_office_id: Optional[int] = None  # Ahora es opcional
    intern: Optional[str] = None  # Ahora es opcional
    page: int

class MaintenanceList(BaseModel):
    branch_office_id: Optional[int] = None  # Ahora es opcional
    page: int

class SearchCashier(BaseModel):
    branch_office_id: Optional[int] = None  # Ahora es opcional
    cashier_id: Optional[str] = None  # Ahora es opcional
    page: int

class UserList(BaseModel):
    rut: Optional[str] = None  # Ahora es opcional
    page: int

class StoreCashier(BaseModel):
    cashier: str
    branch_office_id: int
    getaway_machine_id: Optional[int] = None
    transbank_status_id: Optional[int] = None
    visibility_status_id: Optional[int] = None
    folio_segment_id: Optional[int] = None
    anydesk: Optional[str] = None
    rustdesk: Optional[str] = None

class UpdateCashier(BaseModel):
    cashier: str
    branch_office_id: int
    getaway_machine_id: Optional[int] = None
    transbank_status_id: Optional[int] = None
    visibility_status_id: Optional[int] = None
    folio_segment_id: Optional[int] = None
    anydesk: Optional[str] = None
    rustdesk: Optional[str] = None

class DepositList(BaseModel):
    branch_office_id: Optional[int] = None  # Ahora es opcional
    since: Optional[str] = None  # Ahora es opcional
    until: Optional[str] = None  # Ahora es opcional
    status_id: Optional[int] = None  # Ahora es opcional
    page: int

class StoreCollection(BaseModel):
    branch_office_id: int
    cashier_id: int
    cash_gross_amount: int
    cash_net_amount: int
    card_gross_amount: int
    card_net_amount: int
    total_tickets: int
    added_date: str

class ManualStoreCollection(BaseModel):
    branch_office_id: int
    cashier_id: int
    cash_gross_amount: int
    cash_net_amount: int
    card_gross_amount: int
    card_net_amount: int
    total_tickets: int
    added_date: str

class ExpenseType(BaseModel):
    page: int

class StoreManualSeat(BaseModel):
    branch_office_id: int
    expense_type_id: int
    tax_status_id: int
    period: str
    amount: int

class StoreExpenseType(BaseModel):
    expense_type: str
    accounting_account: str
    capitulation_visibility_id: int
    eerr_visibility_id: int
    track_visibility_id: int
    type: int
    group_detail: int

class UpdateExpenseType(BaseModel):
    id: int
    expense_type: str
    accounting_account: str
    capitulation_visibility_id: int
    eerr_visibility_id: int
    track_visibility_id: int
    type: int
    group_detail: int

class GroupDetail(BaseModel):
    page: int

class StoreGroupDetail(BaseModel):
    group_detail: str

class UpdateGroupDetail(BaseModel):
    id: int
    group_detail: str

class UpdateCollection(BaseModel):
    id: int
    cash_gross_amount: int
    cash_net_amount: int
    card_gross_amount: int
    card_net_amount: int
    total_tickets: int
    added_date: str

class ChangeStatusReceivedTributaryDocument(BaseModel):
    id: int
    branch_office_id: int
    expense_type_id: int
    period: str
    status_id: int
    comment: str

class MachineTicketList(BaseModel):
    page: int

class CustomerTicketList(BaseModel):
    page: int

class CustomerTicketBillList(BaseModel):
    page: int

class ReceivedTributaryDocumentList(BaseModel):
    page: int

class SelectRowsToPay(BaseModel):
    id: int

class ReceivedTributaryDocumentToPay(BaseModel):
    payment_type_id: int
    payment_date: str
    comment: str
    selected_bills: List[SelectRowsToPay]  # Corregir la anotación de tipo

class GeneratedCustomerTicketList(BaseModel):
    page: int

class GeneratedCustomerTicketBillList(BaseModel):
    page: int

class RequestCaf(BaseModel):
    amount: int

class ChangeStatusInCustomerBill(BaseModel):
    id: int
    expense_type_id: int
    payment_type_id: int
    payment_date: str
    comment: str

class ChangeStatusInCustomerTicket(BaseModel):
    id: int
    expense_type_id: int
    payment_type_id: int
    payment_date: str
    comment: str

class ChangeStatusInCustomerTicketBill(BaseModel):
    id: int
    expense_type_id: int
    payment_type_id: int
    payment_date: str
    period: str
    comment: str

class CustomerCollection(BaseModel):
    period: str

class GenerateCustomerTicket(BaseModel):
    id: Optional[int] = 0
    branch_office_id: int
    rut: str
    amount: int
    chip_id: int
    will_save: Optional[int] = 0
    rut: Optional[str] = None
    region_id: Optional[int] = None
    commune_id: Optional[int] = None
    customer: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    activity: Optional[str] = None
    address: Optional[str] = None

class ToBeAcceptedCustomerBill(BaseModel):
    id: Optional[int] = 0
    branch_office_id: int
    rut: str
    amount: int
    chip_id: int
    rut: Optional[str] = None
    region_id: Optional[int] = None
    commune_id: Optional[int] = None
    customer: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    activity: Optional[str] = None
    address: Optional[str] = None
    will_save: Optional[int] = 0

class ToBeAcceptedCustomerTicket(BaseModel):
    id: Optional[int] = 0
    branch_office_id: int
    rut: str
    amount: int
    chip_id: int
    rut: Optional[str] = None
    region_id: Optional[int] = None
    commune_id: Optional[int] = None
    customer: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    activity: Optional[str] = None
    address: Optional[str] = None
    will_save: Optional[int] = 0

class ToBeAcceptedCustomerTicketBill(BaseModel):
    id: Optional[int] = 0
    branch_office_id: int
    rut: str
    amount: int
    chip_id: int
    rut: Optional[str] = None
    region_id: Optional[int] = None
    commune_id: Optional[int] = None
    customer: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    activity: Optional[str] = None
    address: Optional[str] = None
    will_save: Optional[int] = 0

class GenerateCustomerCreditNoteTicket(BaseModel):
    id: int
    reason_id: int
    
class MachineTicketSearch(BaseModel):
    branch_office_id: Optional[int] = None
    dte_type_id: Optional[int] = None
    dte_version_id: Optional[int] = None
    amount: Optional[int] = None
    folio: Optional[int] = None
    since: Optional[str] = None
    until: Optional[str] = None
    page: int

class GenerateMachineCreditNoteTicket(BaseModel):
    id: int
    reason_id: int

class GenerateCustomerCreditNoteTicketBill(BaseModel):
    id: int
    reason_id: int

class GenerateCustomerCreditNoteBill(BaseModel):
    id: int
    reason_id: int

class CustomerBillList(BaseModel):
    page: int

class GeneratedCustomerBillList(BaseModel):
    page: int

class CustomerBillSearch(BaseModel):
    branch_office_id: Optional[int] = None
    rut: Optional[str] = None
    customer: Optional[str] = None
    status_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    customer: Optional[str] = None
    page: int

class CollectionSearch(BaseModel):
    branch_office_id: Optional[int] = None
    cashier_id: Optional[int] = None
    added_date: Optional[str] = None
    page: int

class CustomerTicketSearch(BaseModel):
    branch_office_id: Optional[int] = None
    rut: Optional[str] = None
    customer: Optional[str] = None
    status_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    customer: Optional[str] = None
    page: int

class CustomerTicketBillSearch(BaseModel):
    branch_office_id: Optional[int] = None
    rut: Optional[str] = None
    status_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    customer: Optional[str] = None
    page: int

class GenerateCustomerBill(BaseModel):
    id: Optional[int] = 0
    branch_office_id: int
    rut: str
    amount: int
    chip_id: int
    will_save: Optional[int] = 0
    rut: Optional[str] = None
    region_id: Optional[int] = None
    commune_id: Optional[int] = None
    customer: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    activity: Optional[str] = None
    address: Optional[str] = None

class FolioList(BaseModel):
    page: int

class CafList(BaseModel):
    page: int

class PayrollItemList(BaseModel):
    page: int

class AlertList(BaseModel):
    rut: int
    page: int

class HonoraryList(BaseModel):
    page: int
    branch_office_id: Optional[int] = None
    rut: Optional[str] = None