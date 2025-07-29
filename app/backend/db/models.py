from app.backend.db.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Float, Boolean, Text, Numeric
from datetime import datetime

class BranchOfficeModel(Base):
    __tablename__ = 'branch_offices'

    id = Column(Integer, primary_key=True)
    branch_office = Column(String(255))
    address = Column(String(255))
    region_id = Column(Integer)
    commune_id = Column(Integer)
    segment_id = Column(Integer)
    zone_id = Column(Integer)
    principal_id = Column(Integer)
    getaway_machine_id = Column(Integer)
    status_id = Column(Integer)
    visibility_id = Column(Integer)
    basement_id = Column(Integer)
    opening_date = Column(Integer)
    dte_code = Column(Integer)
    principal_supervisor = Column(Integer)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class DemarcationModel(Base):
    __tablename__ = 'demarcations'

    id = Column(Integer, primary_key=True)
    branch_office_id = Column(Integer)
    material_costs = Column(Integer)
    labor_costs = Column(Integer)
    made_arrows = Column(Integer)
    made_pedestrian_crossing = Column(Integer)
    made_disability = Column(Integer)
    made_island = Column(Integer)
    made_pregnant = Column(Integer)
    made_wall = Column(Integer)
    file_made_arrows = Column(String(255))
    file_made_pedestrian_crossing = Column(String(255))
    file_made_disability = Column(String(255))
    file_made_island = Column(String(255))
    file_made_pregnant = Column(String(255))
    file_made_wall = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class SupplierModel(Base):
    __tablename__ = 'suppliers'

    id = Column(Integer, primary_key=True)
    rut = Column(String(255))
    supplier = Column(String(255))

class Supplier2Model(Base):
    __tablename__ = 'suppliers2'

    id = Column(Integer, primary_key=True)
    rut = Column(String(255))
    supplier = Column(String(255))

class ExpenseTypeModel(Base):
    __tablename__ = 'expense_types'

    id = Column(Integer, primary_key=True)
    capitulation_visibility_id = Column(Integer)
    accounting_account = Column(String(255))
    eerr_visibility_id = Column(Integer)
    track_visibility_id = Column(Integer)
    expense_type = Column(String(255))
    accounting_account = Column(String(255))
    type = Column(Integer)
    group_detail = Column(Integer)

class GroupDetailModel(Base):
    __tablename__ = 'group_details'

    id = Column(Integer, primary_key=True)
    group_detail = Column(String(255))

class ZoneModel(Base):
    __tablename__ = 'zones'

    id = Column(Integer, primary_key=True)
    zone = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class GenderModel(Base):
    __tablename__ = 'genders'

    id = Column(Integer, primary_key=True)
    gender = Column(String(255))
    social_law_code = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class MeshDatumModel(Base):
    __tablename__ = 'mesh_data'

    id = Column(Integer, primary_key=True)
    turn_id = Column(Integer)
    document_employee_id = Column(Integer)
    rut = Column(Integer)
    date = Column(Date())
    total_hours = Column(String(255))
    start = Column(String(255))
    end = Column(String(255))
    week = Column(Integer)
    week_day = Column(Integer)
    period = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class MeshModel(Base):
    __tablename__ = 'meshes'

    id = Column(Integer, primary_key=True)
    rut = Column(Integer)
    period = Column(String(255))
    added_date = Column(DateTime())
class MeshDetailModel(Base):
    __tablename__ = 'mesh_details'

    id = Column(Integer, primary_key=True)
    mesh_id = Column(Integer)
    turn_id = Column(Integer)
    week_id = Column(Integer)
    is_working = Column(Integer)
    is_sunday = Column(Integer)
    rut = Column(Integer)
    date = Column(DateTime())
    added_date = Column(DateTime())
class HolidayModel(Base):
    __tablename__ = 'holidays'

    id = Column(Integer, primary_key=True)
    holiday_type_id = Column(Integer)
    inalienable_id = Column(Integer)
    holiday = Column(String(255))
    date = Column(DateTime())

class PreEmployeeTurnModel(Base):
    __tablename__ = 'pre_employees_turns'

    id = Column(Integer, primary_key=True)
    turn_id = Column(Integer)
    rut = Column(Integer)
    start_date = Column(Date())
    end_date = Column(Date())
    period = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class NationalityModel(Base):
    __tablename__ = 'nationalities'

    id = Column(Integer, primary_key=True)
    nationality = Column(String(255))
    social_law_code = Column(Integer)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

    def as_dict(self):
        return {
            "id": self.id,
            "nationality": self.nationality,
            "previred_code": self.previred_code,
            "added_date": self.added_date.strftime('%Y-%m-%d %H:%M:%S') if self.added_date else None,
            "updated_date": self.updated_date.strftime('%Y-%m-%d %H:%M:%S') if self.updated_date else None,
        }

class PentionModel(Base):
    __tablename__ = 'pentions'

    id = Column(Integer, primary_key=True)
    pention = Column(String(255))
    social_law_code = Column(Integer)
    rut = Column(String(255))
    amount = Column(String(255))
    previred_code = Column(Integer)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class BankModel(Base):
    __tablename__ = 'banks'

    id = Column(Integer, primary_key=True)
    bank = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

    def as_dict(self):
        return {
            "id": self.id,
            "visibility_id": self.visibility_id,
            "bank": self.bank,
            "added_date": self.added_date.strftime('%Y-%m-%d %H:%M:%S') if self.added_date else None,
            "updated_date": self.updated_date.strftime('%Y-%m-%d %H:%M:%S') if self.updated_date else None,
        }

class AccountTypeModel(Base):
    __tablename__ = 'account_types'

    id = Column(Integer, primary_key=True)
    account_type = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class SupervisorModel(Base):
    __tablename__ = 'supervisors'

    id = Column(Integer, primary_key=True)
    branch_office_id = Column(Integer, ForeignKey('branch_offices.id'))
    rut = Column(Integer)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class NewModel(Base):
    __tablename__ = 'news'

    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    description = Column(Text())
    markdown_description = Column(Text())
    picture = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class RegionModel(Base):
    __tablename__ = 'regions'

    id = Column(Integer, primary_key=True)
    region = Column(String(255))    
    region_remuneration_code = Column(Integer) 
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class TotalVacationDaysModel(Base):
    __tablename__ = 'total_vacation_days'

    id = Column(Integer, primary_key=True)
    total_days = Column(Integer)
    total_no_valid_days = Column(Integer)
    total_employee_vacation_days = Column(Integer)

class EmployeeModel(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True)
    rut = Column(Integer)
    visual_rut = Column(String(20))
    names = Column(String(255))
    father_lastname = Column(String(255))
    mother_lastname = Column(String(255))
    gender_id = Column(Integer)
    nationality_id = Column(Integer)
    signature_type_id = Column(Integer)
    personal_email = Column(String(255))
    cellphone = Column(String(100))
    born_date = Column(Date())
    picture = Column(String(255))
    signature = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class TurnModel(Base):
    __tablename__ = 'turns'

    id = Column(Integer, primary_key=True)
    employee_type_id = Column(Integer, ForeignKey('employee_types.id'))
    group_id = Column(Integer)
    group_day_id = Column(Integer)
    free_day_group_id = Column(Integer)
    visibility_id = Column(Integer)
    turn = Column(String(255))
    working = Column(String(255))
    breaking = Column(String(255))
    start = Column(String(255))
    end = Column(String(255))
    start_entry_time_threshold = Column(String(255))
    end_entry_time_threshold = Column(String(255))
    start_exit_time_threshold = Column(String(255))
    end_exit_time_threshold = Column(String(255))
    start_collation_time_threshold = Column(String(255))
    end_collation_time_threshold = Column(String(255))
    total_week_hours = Column(Integer)
    day_hours = Column(Integer)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class ScheduleModel(Base):
    __tablename__ = 'schedule'

    id = Column(Integer, primary_key=True)
    turn_id = Column(Integer)
    week_schedule_id = Column(Integer)
    horary_name = Column(String(255))
    start = Column(String(255))
    end = Column(String(255))
    day = Column(Integer)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class FolioModel(Base):
    __tablename__ = 'folios'
    id = Column(Integer, primary_key=True, autoincrement=True)
    folio = Column(Integer)
    branch_office_id = Column(Integer)
    cashier_id = Column(Integer)
    folio_segment_id = Column(Integer)
    requested_status_id = Column(Integer)
    used_status_id = Column(Integer)
    billed_status_id = Column(Integer)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class FolioReportModel(Base):
    __tablename__ = 'folio_report'
    id = Column(Integer, primary_key=True, autoincrement=True)
    cashier = Column(String(255))
    branch_office = Column(String(255))
    rustdesk = Column(String(255))
    anydesk = Column(String(255))
    available_folios = Column(Integer)

class FolioQuantityPerCashierModel(Base):
    __tablename__ = 'total_folios_per_cashier'
    id = Column(Integer, primary_key=True, autoincrement=True)
    cashier = Column(String(255))
    branch_office = Column(String(255))
    rustdesk = Column(String(255))
    anydesk = Column(String(255))
    available_folios = Column(Integer)

class RemunerationModel(Base):
    __tablename__ = 'remunerations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    branch_office_id = Column(Integer)
    accounting_account = Column(Integer)
    amount = Column(String(255))
    period = Column(String(255))
    added_date = Column(DateTime())

class CashierModel(Base):
    __tablename__ = 'cashiers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    branch_office_id = Column(Integer)
    getaway_machine_id = Column(Integer)
    folio_segment_id = Column(Integer)
    cashier = Column(String(255))
    anydesk = Column(String(255))
    rustdesk = Column(String(255))
    transbank_status_id = Column(Integer)
    visibility_status_id = Column(Integer)
    available_folios = Column(Integer)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class LatestUpdateCashierModel(Base):
    __tablename__ = 'latest_update_cashiers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    cashier = Column(String(255))
    anydesk = Column(String(255))
    rustdesk = Column(String(255))
    last_updated_date = Column(String(255))

class TransbankTotalModel(Base):
    __tablename__ = 'transbank_total'
    id = Column(Integer, primary_key=True, autoincrement=True)
    branch_office_id = Column(Integer)
    total = Column(Integer)
    total_tickets = Column(Integer)
    added_date = Column(Date())

class TotalGeneralCollectionModel(Base):
    __tablename__ = 'total_general_collections'
    id = Column(Integer, primary_key=True, autoincrement=True)
    branch_office_id = Column(Integer)
    cashier_id = Column(Integer)
    total = Column(Integer)
    card_total_collections = Column(Integer)
    total_tickets = Column(Integer)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class TotalCollectionModel(Base):
    __tablename__ = 'total_collections'
    id = Column(Integer, primary_key=True, autoincrement=True)
    branch_office_id = Column(Integer)
    cashier_id = Column(Integer)
    cash_total = Column(Integer)
    card_total = Column(Integer)
    total_tickets = Column(Integer)
    added_date = Column(DateTime())

class TotalDetailCollectionModel(Base):
    __tablename__ = 'total_detail_collections'
    id = Column(Integer, primary_key=True, autoincrement=True)
    branch_office_id = Column(Integer)
    cashier_id = Column(Integer)
    cash_total = Column(Integer)
    card_total = Column(Integer)
    total_tickets = Column(Integer)
    dtes_cash_total = Column(Integer)
    dtes_card_total = Column(Integer)
    dtes_total_tickets = Column(Integer)
    added_date = Column(DateTime())

class DteModel(Base):
    __tablename__ = 'dtes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    branch_office_id = Column(Integer)
    dte_version_id = Column(Integer)
    cashier_id = Column(Integer)
    dte_type_id = Column(Integer)
    chip_id = Column(Integer)
    status_id = Column(Integer)
    expense_type_id = Column(Integer)
    payment_type_id = Column(Integer)
    reason_id = Column(Integer)
    payment_date = Column(String)
    rut = Column(String)
    folio = Column(Integer)
    denied_folio = Column(Integer)
    cash_amount = Column(Integer)
    card_amount = Column(Integer)
    subtotal = Column(Integer)
    tax = Column(Integer)
    discount = Column(Integer)
    payment_amount = Column(Integer)
    total = Column(Integer)
    ticket_serial_number = Column(Integer)
    ticket_hour = Column(String)
    ticket_transaction_number = Column(Integer)
    ticket_dispenser_number = Column(Integer)
    ticket_number = Column(Integer)
    ticket_station_number = Column(Integer)
    ticket_sa = Column(String)
    ticket_correlative = Column(Integer)
    entrance_hour = Column(String)
    exit_hour = Column(String)
    period = Column(String)
    comment = Column(String)
    payment_comment = Column(String)
    payment_number = Column(String)
    support = Column(String)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class UserModel(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    rol_id = Column(Integer, ForeignKey('rols.id'))
    rut = Column(Integer)
    branch_office_id = Column(Integer)
    full_name = Column(String(255))
    email = Column(String(255))
    phone = Column(Text())
    hashed_password = Column(Text())
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class CapitulationModel(Base):
    __tablename__ = 'capitulations'

    id = Column(Integer, primary_key=True)
    document_date = Column(String(255))
    status_id = Column(Integer)
    supplier_rut = Column(String(255))
    document_number = Column(String(255))
    document_type_id = Column(Integer)
    capitulation_type_id = Column(Integer)
    branch_office_id = Column(Integer)
    expense_type_id = Column(Integer)
    user_rut = Column(String(255))
    description = Column(String(255))
    amount = Column(Integer)
    support = Column(String(255))
    why_was_rejected = Column(String(255))
    payment_date = Column(String(255))
    payment_number = Column(String(255))
    payment_support = Column(String(255))
    period = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class TotalAcceptedCapitulations(Base):
    __tablename__ = 'total_accepted_capitulations'

    id = Column(Integer, primary_key=True)
    rut = Column(String(255))
    full_name = Column(String(255))
    amount = Column(Integer)

class CashReserveModel(Base):
    __tablename__ = 'cash_reserves'

    id = Column(Integer, primary_key=True)
    branch_office_id = Column(Integer)
    cashier_id = Column(Integer)
    amount = Column(Integer)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class IntershipModel(Base):
    __tablename__ = 'interships'

    id = Column(Integer, primary_key=True)
    branch_office_id = Column(Integer)
    intern = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class EmployeeIntershipModel(Base):
    __tablename__ = 'employees_interships'

    id = Column(Integer, primary_key=True)
    branch_office_id = Column(Integer)
    intern = Column(String(255))
    observations = Column(String(255))
    support = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class EmployeeIntershipAnswerModel(Base):
    __tablename__ = 'employees_interships_answers'

    id = Column(Integer, primary_key=True)
    intership_id = Column(Integer)
    question_id = Column(Integer)
    answer_id = Column(Integer)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class IntershipAnswerModel(Base):
    __tablename__ = 'interships_answers'

    id = Column(Integer, primary_key=True)
    intership_id = Column(Integer)
    question_id = Column(Integer)
    answer_id = Column(Integer)
    observation = Column(String(255))
    support = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class ContractTypeModel(Base):
    __tablename__ = 'contract_type'

    id = Column(Integer, primary_key=True)
    contract_type = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class ContractTypesModel(Base):
    __tablename__ = 'contract_types'

    id = Column(Integer, primary_key=True)
    contract_type = Column(String(255))

class TaxModel(Base):
    __tablename__ = 'taxes'

    id = Column(Integer, primary_key=True)
    period = Column(String(255))
    support = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class MonthModel(Base):
    __tablename__ = 'months'

    id = Column(Integer, primary_key=True)
    month = Column(Integer)

class ContractModel(Base):
    __tablename__ = 'contracts'

    id = Column(Integer, primary_key=True)
    branch_office_id = Column(Integer)
    contract_type_id = Column(Integer)
    rut = Column(String(255))
    client = Column(String(255))
    start_date = Column(Date())
    end_date = Column(Date())
    renovation_date = Column(Date())
    address = Column(String(255))
    currency = Column(String(255))
    amount = Column(Integer)
    support = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class CustomerModel(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True)
    rut = Column(String(255))
    region_id = Column(Integer)
    commune_id = Column(Integer)
    customer = Column(String(255))
    email = Column(String(255))
    phone = Column(String(255))
    activity = Column(String(255))
    address = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class Customer2Model(Base):
    __tablename__ = 'customers2'

    id = Column(Integer, primary_key=True)
    rut = Column(String(255))
    region_id = Column(Integer)
    commune_id = Column(Integer)
    customer = Column(String(255))
    email = Column(String(255))
    phone = Column(String(255))
    activity = Column(String(255))
    address = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class CivilStateModel(Base):
    __tablename__ = 'civil_states'

    id = Column(Integer, primary_key=True)
    civil_state = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class UniformModel(Base):
    __tablename__ = 'uniforms'

    id = Column(Integer, primary_key=True)
    uniform_type_id = Column(Integer, ForeignKey('uniform_types.id'))
    size = Column(String(255))
    rut = Column(Integer)
    delivered_date = Column(Date())
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class EmployeeTypeModel(Base):
    __tablename__ = 'employee_types'

    id = Column(Integer, primary_key=True)
    employee_type = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class LetterTypeModel(Base):
    __tablename__ = 'letter_types'

    id = Column(Integer, primary_key=True)
    letter_type = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PayrollOtherIndicatorModel(Base):
    __tablename__ = 'payroll_other_indicators'

    id = Column(Integer, primary_key=True)
    other_type_id = Column(Integer)
    other_value = Column(String(255))
    period = Column(String(255))
    added_date = Column(DateTime, default=datetime.now)
    updated_date = Column(DateTime, onupdate=datetime.now)

class EmployeeLaborDatumModel(Base):
    __tablename__ = 'employee_labor_data'

    id = Column(Integer, primary_key=True)
    rut = Column(Integer)
    contract_type_id = Column(Integer, ForeignKey('contract_type.id'))
    branch_office_id = Column(Integer, ForeignKey('branch_offices.id'))
    address = Column(String(255))
    region_id = Column(Integer, ForeignKey('regions.id'))
    commune_id = Column(Integer, ForeignKey('communes.id'))
    civil_state_id = Column(Integer, ForeignKey('civil_states.id'))
    health_id = Column(Integer, ForeignKey('healths.id'))
    pention_id = Column(Integer, ForeignKey('pentions.id'))
    job_position_id = Column(Integer, ForeignKey('job_positions.id'))
    extra_health_payment_type_id = Column(Integer)
    employee_type_id = Column(Integer, ForeignKey('employee_types.id'))
    regime_id = Column(Integer, ForeignKey('regimes.id'))
    status_id = Column(Integer)
    health_payment_id = Column(Integer)
    entrance_pention  = Column(Date())
    entrance_company  = Column(Date())
    entrance_health = Column(Date())
    exit_company  = Column(Date())
    salary = Column(Integer)
    collation = Column(Integer)
    locomotion = Column(Integer)
    extra_health_amount = Column(String(255))
    apv_payment_type_id = Column(Integer)
    apv_amount = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class EmployeeExtraModel(Base):
    __tablename__ = 'employee_extras'

    id = Column(Integer, primary_key=True)
    rut = Column(Integer)
    extreme_zone_id = Column(Integer)
    employee_type_id = Column(Integer, ForeignKey('employee_types.id'))
    young_job_status_id = Column(Integer)
    be_paid_id = Column(Integer)
    suplemental_health_insurance_id = Column(Integer)
    pensioner_id = Column(Integer)
    disability_id = Column(Integer)
    suplemental_health_insurance_id = Column(Integer)
    progressive_vacation_level_id = Column(Integer)
    recognized_years = Column(Integer)
    progressive_vacation_status_id = Column(Integer)
    progressive_vacation_date = Column(Date())
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class OldEmployeeExtraModel(Base):
    __tablename__ = 'old_employee_extras'

    id = Column(Integer, primary_key=True)
    rut = Column(Integer)
    extreme_zone_id = Column(Integer)
    employee_type_id = Column(Integer, ForeignKey('employee_types.id'))
    young_job_status_id = Column(Integer)
    be_paid_id = Column(Integer)
    suplemental_health_insurance_id = Column(Integer)
    pensioner_id = Column(Integer)
    disability_id = Column(Integer)
    suplemental_health_insurance_id = Column(Integer)
    progressive_vacation_level_id = Column(Integer)
    recognized_years = Column(Integer)
    progressive_vacation_status_id = Column(Integer)
    progressive_vacation_date = Column(Date())
    added_date = Column(DateTime())
    updated_date = Column(DateTime())
class RegimeModel(Base):
    __tablename__ = 'regimes'

    id = Column(Integer, primary_key=True)
    regime = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class EmployeeViewModel(Base):
    __tablename__ = 'employee_details'
    __table_args__ = {'info': {'is_view': True}}  # Indica que es una vista

    id = Column(Integer, primary_key=True)
    rut = Column(Integer)
    visual_rut = Column(String(20))
    names = Column(String(255))
    father_lastname = Column(String(255))
    mother_lastname = Column(String(255))
    nickname = Column(String(255))
    gender_id = Column(Integer)
    gender = Column(String(255))
    nationality_id = Column(Integer)
    nationality = Column(String(255))
    personal_email = Column(String(255))
    cellphone = Column(String(100))
    born_date = Column(Date())
    picture = Column(String(255))
    signature = Column(String(255))
    contract_type_id = Column(Integer, ForeignKey('contract_types.id'))
    contract_type = Column(String(255))
    branch_office_id = Column(Integer, ForeignKey('branch_offices.id'))
    branch_office = Column(String(255))
    address = Column(String(255))
    region_id = Column(Integer, ForeignKey('regions.id'))
    region = Column(String(255))
    commune_id = Column(Integer, ForeignKey('communes.id'))
    commune = Column(String(255))
    civil_state_id = Column(Integer, ForeignKey('civil_states.id'))
    civil_state = Column(String(255))
    health_id = Column(Integer, ForeignKey('healths.id'))
    health = Column(String(255))
    pention_id = Column(Integer, ForeignKey('pentions.id'))
    pention = Column(String(255))
    job_position_id = Column(Integer, ForeignKey('job_positions.id'))
    job_position = Column(String(255))
    extreme_zone_id = Column(Integer, ForeignKey('extreme_zones.id'))
    employee_type_id = Column(Integer, ForeignKey('employee_types.id'))
    regime_id = Column(Integer, ForeignKey('regimes.id'))
    status_id = Column(Integer)
    health_payment_id = Column(Integer, ForeignKey('health_payments.id'))
    entrance_pention  = Column(Date())
    entrance_company  = Column(Date())
    entrance_health = Column(Date())
    exit_company  = Column(Date())
    salary = Column(Integer)
    collation = Column(Integer)
    locomotion = Column(Integer)
    company_email = Column(String(255))
    extra_health_amount = Column(String(255))
    apv_payment_type_id = Column(Integer, ForeignKey('apv_payment_types.id'))
    apv_amount = Column(String(255))
    young_job_status_id = Column(Integer)
    be_paid_id = Column(Integer)
    suplemental_health_insurance_id = Column(Integer)
    pensioner_id = Column(Integer)
    disability_id = Column(Integer)
    suplemental_health_insurance_id = Column(Integer)
    progressive_vacation_level_id = Column(Integer)
    recognized_years = Column(Integer)
    progressive_vacation_status_id = Column(Integer)
    progressive_vacation_date = Column(Date())
    progressive_vacation_level_id = Column(Integer)

class HonoraryReasonModel(Base):
    __tablename__ = 'honorary_reasons'

    id = Column(Integer, primary_key=True)
    honorary_reason = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class CommuneModel(Base):
    __tablename__ = 'communes'

    id = Column(Integer, primary_key=True)
    region_id = Column(Integer)
    commune = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class AlertTypeModel(Base):
    __tablename__ = 'alert_types'

    id = Column(Integer, primary_key=True)
    alert_type = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class AlertModel(Base):
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True)
    alert_user_id = Column(Integer)
    alert_type_id = Column(Integer)
    status_id = Column(Integer)
    added_date = Column(Date())
    updated_date = Column(Date())

class IndicatorType(Base):
    __tablename__ = 'indicator_types'

    id = Column(Integer, primary_key=True)
    indicator_type = Column(Integer)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PayrollIndicatorModel(Base):
    __tablename__ = 'payroll_indicators'

    id = Column(Integer, primary_key=True)
    indicator_id = Column(Integer)
    indicator_type_id = Column(Integer)
    period = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PayrollUfIndicatorModel(Base):
    __tablename__ = 'payroll_uf_indicators'

    id = Column(Integer, primary_key=True)
    uf_value_current_month = Column(Float)
    uf_value_last_month = Column(Float)
    period = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PayrollUtmUtaIndicatorModel(Base):
    __tablename__ = 'payroll_utm_uta_indicators'

    id = Column(Integer, primary_key=True)
    utm_value_current_month = Column(Float)
    uta_value_current_month = Column(Float)
    period = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PayrollTaxableIncomeCapIndicatorModel(Base):
    __tablename__ = 'payroll_taxable_income_cap_indicators'

    id = Column(Integer, primary_key=True)
    afp = Column(Integer)
    ips = Column(Integer)
    unemployment = Column(Integer)
    period = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PayrollMiniumTaxableIncomeIndicatorModel(Base):
    __tablename__ = 'payroll_minium_taxable_income_indicators'

    id = Column(Integer, primary_key=True)
    dependent_independent_workers = Column(Float)
    under_18_over_65 = Column(Float)
    particular_home = Column(Float)
    no_remunerations = Column(Float)
    period = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PayrollVoluntaryPrevitionalIndicatorModel(Base):
    __tablename__ = 'payroll_voluntary_previtional_indicators'

    id = Column(Integer, primary_key=True)
    voluntary_pension_savings_monthly = Column(Float)
    voluntary_pension_savings_annual = Column(Float)
    period = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PayrollAgreedDepositIndicatorModel(Base):
    __tablename__ = 'payroll_agreed_deposit_indicators'

    id = Column(Integer, primary_key=True)
    agreed_deposit = Column(Float)
    period = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PayrollUmploymentInsuranceIndicatorModel(Base):
    __tablename__ = 'payroll_umployment_insurance_indicators'

    id = Column(Integer, primary_key=True)
    contract_type_id = Column(Integer)
    worker = Column(Float)
    employer = Column(Float)
    period = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PayrollAfpQuoteIndicatorModel(Base):
    __tablename__ = 'payroll_afp_quote_indicators'

    id = Column(Integer, primary_key=True)
    pention_id = Column(Integer)
    dependent_rate_afp = Column(Float)
    dependent_sis = Column(Float)
    independent_rate_afp = Column(Float)
    period = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PayrollPeriodModel(Base):
    __tablename__ = 'payroll_periods'

    id = Column(Integer, primary_key=True)
    period = Column(String(255))
    opened = Column(DateTime())
    closed = Column(DateTime())
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PayrollEmployeeModel(Base):
    __tablename__ = 'payroll_employees'

    id = Column(Integer, primary_key=True)
    rut = Column(Integer)
    visual_rut = Column(String(255))
    period = Column(String(255))
    contract_type_id = Column(Integer)
    branch_office_id = Column(Integer)
    health_id = Column(Integer)
    pention_id = Column(Integer)
    employee_type_id = Column(Integer)
    regime_id = Column(Integer)
    health_payment_id = Column(Integer)
    extra_health_payment_type_id = Column(Integer)
    apv_payment_type_id = Column(Integer)
    names = Column(String(255))
    father_lastname = Column(String(255))
    mother_lastname = Column(String(255))
    entrance_company = Column(String(255))
    exit_company = Column(String(255))
    salary = Column(Integer)
    collation = Column(Integer)
    locomotion = Column(Integer)
    extra_health_amount = Column(String(255))
    apv_amount = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class DteSettingModel(Base):
    __tablename__ = 'dte_settings'

    id = Column(Integer, primary_key=True)
    folio_quantity_to_send = Column(Integer)
    folio_quantity_sent = Column(Integer)
    folio_quantity_limit = Column(Integer)
    status = Column(Integer)
    last_folio_sent_date = Column(DateTime())

class DteBackgroundModel(Base):
    __tablename__ = 'dte_backgrounds'

    id = Column(Integer, primary_key=True)
    branch_office_id = Column(Integer)
    cashier_id = Column(Integer)
    status_assigned_id = Column(Integer)
    status_used_id = Column(Integer)
    status_sii_id = Column(Integer)
    track_id = Column(Integer)
    folio = Column(Integer)
    sii_date = Column(DateTime())
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PayrollCalculatedEmployeeModel(Base):
    __tablename__ = 'payroll_calculated_employees'

    id = Column(Integer, primary_key=True)
    employee_quantity = Column(Integer)
    period = Column(String(255))

class CollectionModel(Base):
    __tablename__ = 'collections'

    id = Column(Integer, primary_key=True)
    branch_office_id = Column(Integer)
    cashier_id = Column(Integer)
    cash_gross_amount = Column(Integer)
    cash_net_amount = Column(Integer)
    card_gross_amount = Column(Integer)
    card_net_amount = Column(Integer)
    subscribers = Column(Integer)
    total_tickets = Column(Integer)
    added_date = Column(Date())
    updated_date = Column(DateTime())

class DepositModel(Base):
    __tablename__ = 'deposits'

    id = Column(Integer, primary_key=True)
    branch_office_id = Column(Integer)
    payment_type_id = Column(Integer)
    collection_id = Column(Integer)
    status_id = Column(Integer)
    deposited_amount = Column(Integer)
    payment_number = Column(Integer)
    collection_amount = Column(Integer)
    collection_date = Column(Text)
    support = Column(Text)
    added_date = Column(Date)
    updated_date = Column(Date)

class SocialLawModel(Base):
    __tablename__ = 'social_laws'

    id = Column(Integer, primary_key=True)
    rut = Column(Integer)
    dv = Column(String(255))
    father_lastname = Column(String(255))
    mother_lastname = Column(String(255))
    names = Column(String(255))
    gender = Column(String(255))
    nationality = Column(Integer)
    payment_type = Column(Integer)
    period_since = Column(Integer)
    period_until = Column(Integer)
    regime = Column(String(255))
    employee_type = Column(Integer)
    working_days = Column(Integer)
    line_type = Column(Integer)
    movement_code = Column(Integer)
    date_since = Column(String(255))
    date_until = Column(String(255))
    family_allowance_section = Column(String(255))
    number_simple_loads = Column(Integer)
    number_maternal_loads = Column(Integer)
    number_invalid_loads = Column(Integer)
    number_simple_loads = Column(Integer)
    household_allowance = Column(Integer)
    retroactive_family_allowance = Column(Integer)
    reimbursement_family_charges = Column(Integer)
    young_job_status = Column(Integer)
    pention_code = Column(Integer)
    pention_taxable_income = Column(Integer)
    pention_mandatory_contribution = Column(Integer)
    pention_code = Column(Integer)
    disability_insurance_quote = Column(Integer)
    pention_voluntary_savings = Column(Integer)
    pention_substitute_taxable_income = Column(Integer)
    substitute_agreed_rate = Column(Float)
    substitute_compensation_contribution = Column(Integer)
    substitute_period_numbers = Column(Integer)
    substitute_period_since = Column(String(255))
    substitute_period_until = Column(String(255))

class PayrollFamilyAsignationIndicatorModel(Base):
    __tablename__ = 'payroll_family_asignation_indicators'

    id = Column(Integer, primary_key=True)
    section_id = Column(Integer)
    amount = Column(Float)
    minimum_value_rate = Column(Integer)
    top_value_rate = Column(Integer)
    period = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PayrollSecondCategoryTaxModel(Base):
    __tablename__ = 'payroll_second_category_taxes'

    id = Column(Integer, primary_key=True)
    period = Column(String(255))
    since = Column(String(255))
    until = Column(String(255))
    factor = Column(String(255))
    discount = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PayrollHeavyDutyQuoteIndicatorModel(Base):
    __tablename__ = 'payroll_heavy_duty_quote_indicators'

    id = Column(Integer, primary_key=True)
    duty_type_id = Column(Integer)
    job_position = Column(Float)
    employer = Column(Float)
    worker = Column(Float)
    period = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PayrollCcafIndicatorModel(Base):
    __tablename__ = 'payroll_ccaf_indicators'

    id = Column(Integer, primary_key=True)
    ccaf = Column(String(255))
    fonasa = Column(String(255))
    period = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class HrSettingModel(Base):
    __tablename__ = 'hr_settings'

    id = Column(Integer, primary_key=True)
    percentage_honorary_bill = Column(String(255))
    apigetaway_token = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PayrollManualInputModel(Base):
    __tablename__ = 'payroll_manual_inputs'

    id = Column(Integer, primary_key=True)
    payroll_item_id = Column(Integer)
    rut = Column(Integer)
    amount = Column(Integer)
    period = Column(String(255))
    added_date = Column(DateTime())

class HrFinalDayMonthModel(Base):
    __tablename__ = 'hr_final_day_months'

    id = Column(Integer, primary_key=True)
    end_day = Column(Integer)
    adjustment_day = Column(Integer)

class HonoraryModel(Base):
    __tablename__ = 'honoraries'

    id = Column(Integer, primary_key=True)
    honorary_reason_id = Column(Integer)
    branch_office_id = Column(Integer)
    foreigner_id = Column(Integer)
    bank_id = Column(Integer)
    account_type_id = Column(Integer)
    schedule_id = Column(Integer)
    region_id = Column(Integer)
    commune_id = Column(Integer)
    requested_by = Column(Integer)
    status_id = Column(Integer)
    employee_to_replace = Column(Integer)
    replacement_employee_rut = Column(Integer)
    replacement_employee_full_name = Column(String(255))
    address = Column(String(255))
    account_number = Column(String(255))
    start_date = Column(Date())
    end_date = Column(Date())
    amount = Column(Integer)
    observation = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class UniformTypeModel(Base):
    __tablename__ = 'uniform_types'

    id = Column(Integer, primary_key=True)
    uniform_type = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class SegmentModel(Base):
    __tablename__ = 'segments'

    id = Column(Integer, primary_key=True)
    segment = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class JobPositionModel(Base):
    __tablename__ = 'job_positions'

    id = Column(Integer, primary_key=True)
    job_position = Column(String(255))
    functions = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PatologyTypeModel(Base):
    __tablename__ = 'patology_types'

    id = Column(Integer, primary_key=True)
    patology_type = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class DocumentTypeModel(Base):
    __tablename__ = 'document_types'

    id = Column(Integer, primary_key=True)
    document_type = Column(String(255))
    document_group_id = Column(Integer) 
    order = Column(Integer) 
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class EndDocumentModel(Base):
    __tablename__ = 'end_documents'
    id = Column(Integer, primary_key=True)
    document_employee_id = Column(Integer) 
    causal_id = Column(Integer) 
    rut = Column(Integer) 
    fertility_proportional_days = Column(Integer) 
    voluntary_indemnity = Column(Integer) 
    indemnity_years_service= Column(Integer) 
    substitute_compensation = Column(Integer) 
    fertility_proportional = Column(Integer) 
    total = Column(Integer) 
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class FamilyTypeModel(Base):
    __tablename__ = 'family_types'

    id = Column(Integer, primary_key=True)
    family_type = Column(String(255))
    added_date = Column(DateTime())

class FamilyCoreDatumModel(Base):
    __tablename__ = 'family_core_data'

    id = Column(Integer, primary_key=True)
    family_type_id = Column(Integer, ForeignKey('family_types.id'))
    employee_rut = Column(Integer)
    gender_id = Column(Integer, ForeignKey('genders.id'))
    rut = Column(Integer)
    names = Column(String(255))
    father_lastname = Column(String(255))
    mother_lastname = Column(String(255))
    born_date = Column(DateTime())
    support = Column(Text)
    added_date = Column(DateTime())

class OldFamilyCoreDatumModel(Base):
    __tablename__ = 'old_family_core_data'

    id = Column(Integer, primary_key=True)
    family_type_id = Column(Integer)
    employee_rut = Column(Integer)
    gender_id = Column(Integer)
    rut = Column(String(255))
    names = Column(String(255))
    father_lastname = Column(String(255))
    mother_lastname = Column(String(255))
    born_date = Column(String(255))
    support = Column(Text)
    added_date = Column(DateTime())

class VacationModel(Base):
    __tablename__ = 'vacations'

    id = Column(Integer, primary_key=True)
    document_employee_id = Column(Integer)
    rut = Column(Integer)
    since = Column(Date())
    until = Column(Date())
    days = Column(Integer)
    no_valid_days = Column(Integer)
    support = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

    def to_dict(self):
        return {
            "id": self.id,
            "rut": self.rut,
            "since": str(self.since),
            "since": str(self.since),
            "until": str(self.until),
            "days": self.days,
            "no_valid_days": self.no_valid_days,
            "support": str(self.support),
            "added_date": str(self.added_date),
            "updated_date": str(self.updated_date),
        }
    
class SliderModel(Base):
    __tablename__ = 'slider'

    id = Column(Integer, primary_key=True)
    support = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())
class LogoModel(Base):
    __tablename__ = 'logo'

    id = Column(Integer, primary_key=True)
    support = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())
class AboutUsModel(Base):
    __tablename__ = 'about_us'

    id = Column(Integer, primary_key=True)
    text = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())
class ContactModel(Base):
    __tablename__ = 'contact'

    id = Column(Integer, primary_key=True)
    address = Column(String(255))
    cellphone = Column(String(100))
    email = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())
class BlogModel(Base):
    __tablename__ = 'blog'

    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    description = Column(String(100))
    picture = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())
class PossibleEmployeesModel(Base):
    __tablename__ = 'possible_employees'

    id = Column(Integer, primary_key=True)
    rut = Column(String(100))
    names = Column(String(255))
    father_lastname = Column(String(100))
    mother_lastname = Column(String(100))
    cellphone = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())
class FrecuentQuestionModel(Base):
    __tablename__ = 'frecuent_question'

    id = Column(Integer, primary_key=True)
    question = Column(String(255))
    answer = Column(String(100))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())
    
class ProgressiveVacationModel(Base):
    __tablename__ = 'progressive_vacations'

    id = Column(Integer, primary_key=True)
    document_employee_id = Column(Integer)
    rut = Column(Integer)
    since = Column(Date())
    until = Column(Date())
    days = Column(Integer)
    no_valid_days = Column(Integer)
    support = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PayrollItemValueModel(Base):
    __tablename__ = 'payroll_item_values'

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer)
    rut = Column(Integer)
    period = Column(String(255))
    amount = Column(Integer)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PayrollMonthIndicatorModel(Base):
    __tablename__ = 'payroll_month_indicators'

    id = Column(Integer, primary_key=True)
    month_id = Column(Integer)
    month_value = Column(String(255))
    period = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PayrollItemModel(Base):
    __tablename__ = 'payroll_items'

    id = Column(Integer, primary_key=True)
    item_type_id = Column(Integer)
    classification_id = Column(Integer)
    order_id = Column(Integer)
    disabled_id = Column(Integer)
    item = Column(String(255))
    salary_settlement_name = Column(String(255))
    salary_settlement_location_id = Column(Integer)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class ComplaintModel(Base):
    __tablename__ = 'complaints'

    id = Column(Integer, primary_key=True)
    relationship = Column(String(255))
    incident_place = Column(String(255))
    complaint_type = Column(String(255))
    anonymous = Column(String(255))
    incident_date = Column(String(255))
    incident_place_detail = Column(String(255))
    knowledge = Column(String(255))
    identify = Column(String(255))
    support = Column(String(255))
    description = Column(String(255))
    password = Column(String(255))
    email = Column(String(255))
    status = Column(Integer)
    added_date = Column(DateTime())

class MedicalLicenseModel(Base):
    __tablename__ = 'medical_licenses'

    id = Column(Integer, primary_key=True)
    document_employee_id = Column(Integer)
    medical_license_type_id = Column(Integer, ForeignKey('medical_license_types.id'))
    patology_type_id = Column(Integer, ForeignKey('patology_types.id'))
    period = Column(String(255))
    rut = Column(Integer)
    folio = Column(String(255))
    since = Column(Date())
    until = Column(Date())
    days = Column(Integer)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class OldMedicalLicenseModel(Base):
    __tablename__ = 'old_medical_licenses'

    id = Column(Integer, primary_key=True)
    document_employee_id = Column(Integer)
    medical_license_type_id = Column(Integer )
    patology_type_id = Column(Integer)
    period = Column(String(255))
    rut = Column(Integer)
    folio = Column(String(255))
    since = Column(Date())
    until = Column(Date())
    days = Column(Integer)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class RolModel(Base):
    __tablename__ = 'rols'

    id = Column(Integer, primary_key=True)
    rol = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PrincipalModel(Base):
    __tablename__ = 'principals'

    id = Column(Integer, primary_key=True)
    principal = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class CarbonMonoxideModel(Base):
    __tablename__ = 'carbon_monoxides'

    id = Column(Integer, primary_key=True)
    branch_office_id = Column(Integer)
    measure_value = Column(String(255))
    support = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class BankStatementModel(Base):
    __tablename__ = 'bank_statements'

    id = Column(Integer, primary_key=True)
    bank_statement_type_id = Column(Integer)
    rut = Column(String(255))
    deposit_number = Column(String(255))
    amount = Column(Integer)
    period = Column(String(255))
    deposit_date = Column(String(255))

class TransbankStatementModel(Base):
    __tablename__ = 'transbank_statements'

    id = Column(Integer, primary_key=True)
    branch_office_id = Column(Integer)
    original_date = Column(String(255))
    code = Column(String(255))
    branch_office_name = Column(String(255))
    sale_type = Column(String(255))
    payment_type = Column(String(255))
    card_number = Column(String(255))
    sale_description = Column(String(255))
    amount = Column(String(255))
    value_1 = Column(String(255))
    value_2 = Column(String(255))
    value_3 = Column(String(255))
    value_4 = Column(String(255))
    added_date = Column(DateTime())

class BranchOfficesTransbankStatementsModel(Base):
    __tablename__ = 'branch_offices_transbanks'

    id = Column(Integer, primary_key=True)
    branch_office_id = Column(Integer)
    transbank_code = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class ComparationPendingDtesBankStatementModel(Base):
    __tablename__ = 'comparation_pending_dtes_bank_statements'

    id = Column(Integer, primary_key=True)
    rut = Column(String(255))
    customer = Column(String(255))
    folio = Column(Integer)
    branch_office = Column(String(255))
    amount = Column(Integer)
    bank_statement_type_id = Column(Integer)
    bank_statement_period = Column(String(255))
    bank_statement_amount = Column(Integer)
    bank_statement_rut = Column(String(255))
    deposit_number = Column(String(255))
    deposit_date = Column(String(255))

class ComparationPendingDepositsBankStatementModel(Base):
    __tablename__ = 'comparation_pending_deposits_bank_statements'

    id = Column(Integer, primary_key=True)
    branch_office_id = Column(Integer)
    payment_type_id = Column(Integer)
    collection_id = Column(Integer)
    deposit_id = Column(Integer)
    branch_office = Column(String(255))
    status_id = Column(Integer)
    payment_number = Column(Integer)
    collection_amount = Column(Integer)
    deposited_amount = Column(Integer)
    collection_date = Column(String(255))
    bank_statement_type_id = Column(Integer)
    bank_statement_amount = Column(Integer)
    bank_statement_rut = Column(String(255))
    deposit_number = Column(String(255))

class SinisterModel(Base):
    __tablename__ = 'sinisters'

    id = Column(Integer, primary_key=True)
    branch_office_id = Column(Integer)
    status_id = Column(Integer)
    sinister_type_id = Column(Integer)
    protected_area_id = Column(Integer)
    registered_event_id = Column(Integer)
    notified_security_id = Column(Integer)
    denounced_authorities_id = Column(Integer)
    sinister_date = Column(String(255))
    client_rut = Column(String(255))
    client_name = Column(String(255))
    client_last_name = Column(String(255))
    client_email = Column(String(255))
    client_phone = Column(String(255))
    brand = Column(String(255))
    model = Column(String(255))
    year = Column(String(255))
    patent = Column(String(255))
    color = Column(String(255))
    description = Column(String(255))
    support = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class WhatsappTemplateModel(Base):
    __tablename__ = 'whatsapp_templates'

    id = Column(Integer, primary_key=True)
    title = Column(Text)
    template = Column(Text)

class MaintenanceModel(Base):
    __tablename__ = 'maintenances'

    id = Column(Integer, primary_key=True)
    branch_office_id = Column(Integer)
    maintenance_date = Column(Date())
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class MaintenanceDataModel(Base):
    __tablename__ = 'maintenance_data'

    id = Column(Integer, primary_key=True)
    maintenance_id = Column(Integer)
    file_number = Column(Integer)
    support = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class SettingModel(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    capitulation_close_period = Column(Text)
    capitulation_open_period = Column(Text)
    honorary_open_period = Column(Text)
    honorary_close_period = Column(Text)
    dropbox_token = Column(Text)
    facebook_token = Column(Text)
    simplefactura_token = Column(Text)
    caf_limit = Column(Integer)
    percentage_honorary_bill = Column(Text)
    apigetaway_token = Column(Text)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class AlertUserModel(Base):
    __tablename__ = 'alert_users'

    id = Column(Integer, primary_key=True)
    alert_type_id = Column(Integer)
    user_id = Column(Integer)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class HealthModel(Base):
    __tablename__ = 'healths'

    id = Column(Integer, primary_key=True)
    health_remuneration_code = Column(Integer)
    health = Column(String(255))
    rut = Column(Integer)
    social_law = Column(Integer)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class EmployeeBankAccountModel(Base):
    __tablename__ = 'employees_bank_accounts'

    id = Column(Integer, primary_key=True)
    bank_id = Column(Integer, ForeignKey('banks.id'))
    account_type_id = Column(Integer)
    status_id = Column(Integer)
    rut = Column(Integer)
    account_number = Column(Integer)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class DocumentEmployeeModel(Base):
    __tablename__ = 'documents_employees'

    id = Column(Integer, primary_key=True)
    status_id = Column(Integer)
    document_type_id = Column(Integer, ForeignKey('document_types.id'))
    old_document_status_id = Column(Integer)
    rut = Column(Integer)
    period = Column(String(255))
    support = Column(String(255))
    added_date =  Column(DateTime())
    updated_date = Column(DateTime())

class DocumentEmployeeSignatureModel(Base):
    __tablename__ = 'documents_employees_signatures'

    id = Column(Integer, primary_key=True)
    document_employee_id = Column(Integer)
    rut = Column(Integer)
    added_date =  Column(DateTime())
    updated_date = Column(DateTime())

class OldDocumentEmployeeModel(Base):
    __tablename__ = 'old_documents_employees'

    id = Column(Integer, primary_key=True)
    status_id = Column(Integer)
    document_type_id = Column(Integer)
    rut = Column(Integer)
    support = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class OldVacationModel(Base):
    __tablename__ = 'old_vacations'

    id = Column(Integer, primary_key=True)
    document_employee_id = Column(Integer)
    rut = Column(Integer)
    since = Column(Date())
    until = Column(Date())
    days = Column(Integer)
    no_valid_days = Column(Integer)
    support = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class OldEmployeeModel(Base):
    __tablename__ = 'old_employees'

    id = Column(Integer, primary_key=True)
    rut = Column(Integer)
    visual_rut = Column(String(20))
    names = Column(String(255))
    father_lastname = Column(String(255))
    mother_lastname = Column(String(255))
    gender_id = Column(Integer)
    nationality_id = Column(Integer)
    personal_email = Column(String(255))
    cellphone = Column(String(100))
    born_date = Column(Date())
    picture = Column(String(255))
    signature = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class OldEmployeeLaborDatumModel(Base):
    __tablename__ = 'old_employee_labor_data'

    id = Column(Integer, primary_key=True)
    rut = Column(Integer)
    contract_type_id = Column(Integer )
    branch_office_id = Column(Integer)
    address = Column(String(255))
    region_id = Column(Integer)
    commune_id = Column(Integer)
    civil_state_id = Column(Integer)
    health_id = Column(Integer)
    pention_id = Column(Integer)
    job_position_id = Column(Integer)
    employee_type_id = Column(Integer)
    regime_id = Column(Integer)
    status_id = Column(Integer)
    health_payment_id = Column(Integer)
    apv_payment_type_id = Column(Integer)
    entrance_pention  = Column(Date())
    entrance_company  = Column(Date())
    entrance_health = Column(Date())
    exit_company  = Column(Date())
    salary = Column(Integer)
    collation = Column(Integer)
    locomotion = Column(Integer)
    extra_health_amount = Column(String(255))
    apv_amount = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class PatentModel(Base):
    __tablename__ = 'patents'

    id = Column(Integer, primary_key=True)
    branch_office_id = Column(Integer)
    semester = Column(String(255))
    year = Column(Integer)
    support = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class ClockUserModel(Base):
    __tablename__ = 'clock_users'

    id = Column(Integer, primary_key=True)
    uid = Column(Integer)
    rut = Column(Integer)
    full_name = Column(String(255))
    privilege = Column(Integer)
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class MedicalLicenseTypeModel(Base):
    __tablename__ = 'medical_license_types'

    id = Column(Integer, primary_key=True)
    medical_license_type = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class CausalModel(Base):
    __tablename__ = 'causals'
    
    id = Column(Integer, primary_key=True)
    end_document_status_id = Column(Integer, ForeignKey('end_document_statuses.id'))
    causal = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())

class SinisterReviewModel(Base):
    __tablename__ = 'sinisters_reviews'
    
    id = Column(Integer, primary_key=True)
    sinister_id = Column(Integer)
    sinister_step_type_id = Column(Integer)
    review_description = Column(String(255))
    support = Column(String(255))
    added_date = Column(DateTime())
    updated_date = Column(DateTime())
