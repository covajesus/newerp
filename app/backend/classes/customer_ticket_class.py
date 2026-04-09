from sqlalchemy.orm import Session
from app.backend.db.models import DteModel, CustomerModel, BranchOfficeModel, ExpenseTypeModel
from app.backend.classes.customer_class import CustomerClass
from app.backend.classes.whatsapp_class import WhatsappClass
from app.backend.classes.helper_class import HelperClass
from app.backend.classes.file_class import FileClass
from sqlalchemy import desc
from sqlalchemy.dialects import mysql
from sqlalchemy import or_
from datetime import datetime, timedelta
from fastapi import HTTPException
import requests
import json
import base64
import uuid
from sqlalchemy.sql import func


def _dte_rut_sql_or(rut_column, rut_value):
    """
    El RUT en `dtes.rut` (string) puede guardarse como 27141399-8, 271413998, etc.
    Evita que generate() no encuentre el borrador por formato distinto al del formulario.
    """
    if rut_value is None:
        return rut_column.is_(None)
    raw = str(rut_value).strip()
    if not raw:
        return rut_column == ""
    variants = {raw, raw.upper().replace(".", "").replace(" ", "")}
    s = raw.upper().replace(".", "").replace(" ", "")
    if "-" in s:
        left, right = s.split("-", 1)
        body = "".join(c for c in left if c.isdigit())
        dv = right.strip().upper()[:1] if right else ""
        if body and dv:
            variants.add(f"{body}-{dv}")
            variants.add(f"{body}{dv}")
    digits = "".join(c for c in s if c.isdigit())
    if len(digits) >= 7:
        variants.add(digits)
    clean = [v for v in variants if v is not None and str(v).strip()]
    if len(clean) == 1:
        return rut_column == clean[0]
    return or_(*[rut_column == v for v in clean])


def _ticket_total_from_form(form_data):
    """
    Total a guardar (cash_amount/total), misma convención que store() y pre_generate_ticket:
    - Sin chip: amount es el total.
    - Con chip y will_save==1 (guardar borrador): amount es solo estacionamiento → total = amount+5000.
    - Con chip y will_save!=1 (p. ej. default 0 al generar): amount ya es el total con chip → no sumar 5000 otra vez.
    """
    if getattr(form_data, "chip_id", None) != 1:
        return int(form_data.amount)
    if getattr(form_data, "will_save", 0) == 1:
        return int(form_data.amount) + 5000
    return int(form_data.amount)


def _sync_ticket_dte_amounts_from_form(dte, form_data):
    """
    Al asignar folio (emitir), alinear cash_amount/total/subtotal/IVA con el formulario.
    Si generate() enlaza el borrador por fallback (RUT sin coincidencia de total), el registro
    podía quedar con cash_amount NULL o montos viejos; LibreDTE sí timbra el monto correcto.
    """
    base = _ticket_total_from_form(form_data)
    dte.chip_id = form_data.chip_id
    dte.cash_amount = base
    dte.subtotal = round(base / 1.19)
    dte.tax = base - round(base / 1.19)
    dte.total = base
    cid = getattr(form_data, "category_id", None)
    if cid is not None:
        dte.category_id = cid
    qty = getattr(form_data, "quantity", None)
    if getattr(dte, "category_id", None) == 3 and qty is not None:
        dte.quantity = int(qty)
    else:
        dte.quantity = None


class CustomerTicketClass:
    def __init__(self, db: Session):
        self.db = db
        self.file_class = FileClass(db)  # Crear una instancia de FileClass

    def get_all(self, rol_id = None, rut = None, group=1, page=0, items_per_page=10, period=None):
        try:
            if rol_id == 1 or rol_id == 2:
                # Inicialización de filtros dinámicos
                filters = []

                filters.append(DteModel.dte_version_id == 1)
                filters.append(DteModel.dte_type_id == 39)
                filters.append(DteModel.rut != None)

                if group == 1:
                    filters.append(or_(DteModel.status_id == 1, DteModel.status_id == 2, DteModel.status_id == 3))

                    current_period = datetime.now().strftime('%Y-%m')
                    filters.append(DteModel.period == current_period)

                    # Construir la consulta base con los filtros aplicados
                    query = self.db.query(
                        DteModel.id, 
                        DteModel.branch_office_id, 
                        DteModel.folio, 
                        DteModel.total,
                        DteModel.added_date,
                        DteModel.rut,
                        DteModel.status_id,
                        DteModel.chip_id,
                        CustomerModel.customer,
                        BranchOfficeModel.branch_office
                    ).outerjoin(
                        BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
                    ).outerjoin(
                        CustomerModel, CustomerModel.rut == DteModel.rut
                    ).filter(
                        *filters
                    ).order_by(
                        desc(DteModel.status_id)
                    )
                else:
                    filters.append(or_(DteModel.status_id == 4, DteModel.status_id == 5))
            
                    # Construir la consulta base con los filtros aplicados
                    query = self.db.query(
                        DteModel.id, 
                        DteModel.branch_office_id, 
                        DteModel.folio, 
                        DteModel.total,
                        DteModel.added_date,
                        DteModel.rut,
                        DteModel.status_id,
                        DteModel.chip_id,
                        CustomerModel.customer,
                        BranchOfficeModel.branch_office
                    ).outerjoin(
                        BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
                    ).outerjoin(
                        CustomerModel, CustomerModel.rut == DteModel.rut
                    ).filter(
                        *filters
                    ).order_by(
                        desc(DteModel.folio)
                    )
            elif rol_id == 4:
                # Inicialización de filtros dinámicos
                filters = []

                filters.append(DteModel.dte_version_id == 1)
                filters.append(DteModel.dte_type_id == 39)
                filters.append(DteModel.rut != None)

                if group == 1:
                    filters.append(or_(DteModel.status_id == 1, DteModel.status_id == 2, DteModel.status_id == 3))

                    current_period = datetime.now().strftime('%Y-%m')
                    filters.append(DteModel.period == current_period)

                    # Construir la consulta base con los filtros aplicados
                    query = self.db.query(
                        DteModel.id, 
                        DteModel.branch_office_id, 
                        DteModel.folio, 
                        DteModel.total,
                        DteModel.added_date,
                        DteModel.rut,
                        DteModel.status_id,
                        DteModel.chip_id,
                        CustomerModel.customer,
                        BranchOfficeModel.branch_office
                    ).outerjoin(
                        BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
                    ).outerjoin(
                        CustomerModel, CustomerModel.rut == DteModel.rut
                    ).filter(
                        BranchOfficeModel.principal_supervisor == rut
                    ).filter(
                        *filters
                    ).order_by(
                        desc(DteModel.status_id)
                    )
                else:
                    filters.append(or_(DteModel.status_id == 4, DteModel.status_id == 5))
            
                    # Construir la consulta base con los filtros aplicados
                    query = self.db.query(
                        DteModel.id, 
                        DteModel.branch_office_id, 
                        DteModel.folio, 
                        DteModel.total,
                        DteModel.added_date,
                        DteModel.rut,
                        DteModel.status_id,
                        DteModel.chip_id,
                        CustomerModel.customer,
                        BranchOfficeModel.branch_office
                    ).outerjoin(
                        BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
                    ).outerjoin(
                        CustomerModel, CustomerModel.rut == DteModel.rut
                    ).filter(
                        BranchOfficeModel.principal_supervisor == rut
                    ).filter(
                        *filters
                    ).order_by(
                        desc(DteModel.folio)
                    )

            # Si se solicita paginación
            if page > 0:
                # Calcular el total de registros
                total_items = query.count()
                print(query.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))

                total_pages = (total_items + items_per_page - 1) // items_per_page
                print(total_pages)
                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                # Aplicar paginación en la consulta
                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                # Serializar los datos
                serialized_data = [{
                    "id": dte.id,
                    "rut": dte.rut,
                    "branch_office_id": dte.branch_office_id,
                    "customer": dte.customer,
                    "chip_id": dte.chip_id,
                    "folio": dte.folio,
                    "total": dte.total,
                    "status_id": dte.status_id,
                    "added_date": dte.added_date.strftime('%Y-%m-%d') if dte.added_date else None,
                    "branch_office": dte.branch_office
                } for dte in data]

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }

            # Si no se solicita paginación, traer todos los datos
            else:
                data = query.all()

                # Serializar los datos
                serialized_data = [{
                    "id": dte.id,
                    "rut": dte.rut,
                    "branch_office_id": dte.branch_office_id,
                    "customer": dte.customer,
                    "chip_id": dte.chip_id,
                    "folio": dte.folio,
                    "total": dte.total,
                    "added_date": dte.added_date.strftime('%Y-%m-%d') if dte.added_date else None,
                    "branch_office": dte.branch_office,
                    "status_id": dte.status_id
                } for dte in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}

    def search(self, rol_id = None, supervisor_rut = None, branch_office_id=None, rut=None, customer=None, status_id=None, supervisor_id=None, page=0, items_per_page=10):
        try:
            if rol_id == 1 or rol_id == 2:
                # Filtros: borradores boleta (39), período mes actual. 0 en sucursal = todas.
                filters = []

                if branch_office_id is not None and branch_office_id != "" and branch_office_id != 0:
                    filters.append(DteModel.branch_office_id == branch_office_id)
                if rut is not None and str(rut).strip() != "":
                    filters.append(_dte_rut_sql_or(DteModel.rut, rut))
                if customer is not None and customer != "":
                    filters.append(CustomerModel.customer.like(f"%{customer}%"))
                # Evitar mezclar status_id explícito con status_id < 4 a la vez (contradicciones).
                if status_id is not None and status_id != "":
                    filters.append(DteModel.status_id == status_id)
                else:
                    filters.append(DteModel.status_id < 4)

                filters.append(DteModel.dte_version_id == 1)
                filters.append(DteModel.dte_type_id == 39)
                filters.append(DteModel.rut != None)
                filters.append(DteModel.period == datetime.now().strftime('%Y-%m'))

                if supervisor_id is not None and supervisor_id != "":
                    filters.append(BranchOfficeModel.principal_supervisor == supervisor_id)

                query = self.db.query(
                    DteModel.id,
                    DteModel.branch_office_id,
                    DteModel.folio,
                    DteModel.total,
                    DteModel.added_date,
                    DteModel.rut,
                    DteModel.status_id,
                    DteModel.chip_id,
                    CustomerModel.customer,
                    BranchOfficeModel.branch_office
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
                ).outerjoin(
                    CustomerModel, CustomerModel.rut == DteModel.rut
                ).filter(
                    *filters
                ).order_by(
                    DteModel.folio.desc()
                )

                # Si se solicita paginación
                if page > 0:
                    # Calcular el total de registros
                    total_items = query.count()
                    print(query.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))

                    total_pages = (total_items + items_per_page - 1) // items_per_page
                    print(total_pages)
                    if page < 1 or page > total_pages:
                        return {"status": "error", "message": "Invalid page number"}

                    # Aplicar paginación en la consulta
                    data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                    if not data:
                        return {"status": "error", "message": "No data found"}

                    # Serializar los datos
                    serialized_data = [{
                        "id": dte.id,
                        "rut": dte.rut,
                        "branch_office_id": dte.branch_office_id,
                        "customer": dte.customer,
                        "chip_id": dte.chip_id,
                        "folio": dte.folio,
                        "total": dte.total,
                        "status_id": dte.status_id,
                        "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                        "branch_office": dte.branch_office
                    } for dte in data]

                    return {
                        "total_items": total_items,
                        "total_pages": total_pages,
                        "current_page": page,
                        "items_per_page": items_per_page,
                        "data": serialized_data
                    }

                # Si no se solicita paginación, traer todos los datos
                else:
                    data = query.all()

                    # Serializar los datos
                    serialized_data = [{
                        "id": dte.id,
                        "rut": dte.rut,
                        "branch_office_id": dte.branch_office_id,
                        "customer": dte.customer,
                        "folio": dte.folio,
                        "chip_id": dte.chip_id,
                        "total": dte.total,
                        "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                        "branch_office": dte.branch_office,
                        "status_id": dte.status_id
                    } for dte in data]

                    return {
                        "data": serialized_data
                    }
            elif rol_id == 4:
                filters = []

                if branch_office_id is not None and branch_office_id != "" and branch_office_id != 0:
                    filters.append(DteModel.branch_office_id == branch_office_id)
                if rut is not None and str(rut).strip() != "":
                    filters.append(_dte_rut_sql_or(DteModel.rut, rut))
                if customer is not None and customer != "":
                    filters.append(CustomerModel.customer.like(f"%{customer}%"))
                if status_id is not None and status_id != "":
                    filters.append(DteModel.status_id == status_id)
                else:
                    filters.append(DteModel.status_id < 4)

                filters.append(DteModel.dte_version_id == 1)
                filters.append(DteModel.dte_type_id == 39)
                filters.append(DteModel.rut != None)
                filters.append(DteModel.period == datetime.now().strftime('%Y-%m'))

                query = self.db.query(
                    DteModel.id,
                    DteModel.branch_office_id,
                    DteModel.folio,
                    DteModel.total,
                    DteModel.added_date,
                    DteModel.rut,
                    DteModel.status_id,
                    DteModel.chip_id,
                    CustomerModel.customer,
                    BranchOfficeModel.branch_office
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
                ).outerjoin(
                    CustomerModel, CustomerModel.rut == DteModel.rut
                ).filter(
                    BranchOfficeModel.principal_supervisor == supervisor_rut
                ).filter(
                    *filters
                ).order_by(
                    DteModel.folio.desc()
                )

                # Si se solicita paginación
                if page > 0:
                    # Calcular el total de registros
                    total_items = query.count()
                    print(query.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))

                    total_pages = (total_items + items_per_page - 1) // items_per_page
                    print(total_pages)
                    if page < 1 or page > total_pages:
                        return {"status": "error", "message": "Invalid page number"}

                    # Aplicar paginación en la consulta
                    data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                    if not data:
                        return {"status": "error", "message": "No data found"}

                    # Serializar los datos
                    serialized_data = [{
                        "id": dte.id,
                        "rut": dte.rut,
                        "branch_office_id": dte.branch_office_id,
                        "customer": dte.customer,
                        "chip_id": dte.chip_id,
                        "folio": dte.folio,
                        "total": dte.total,
                        "status_id": dte.status_id,
                        "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                        "branch_office": dte.branch_office
                    } for dte in data]

                    return {
                        "total_items": total_items,
                        "total_pages": total_pages,
                        "current_page": page,
                        "items_per_page": items_per_page,
                        "data": serialized_data
                    }

                # Si no se solicita paginación, traer todos los datos
                else:
                    data = query.all()

                    # Serializar los datos
                    serialized_data = [{
                        "id": dte.id,
                        "rut": dte.rut,
                        "branch_office_id": dte.branch_office_id,
                        "customer": dte.customer,
                        "folio": dte.folio,
                        "chip_id": dte.chip_id,
                        "total": dte.total,
                        "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                        "branch_office": dte.branch_office,
                        "status_id": dte.status_id
                    } for dte in data]

                    return {
                        "data": serialized_data
                    }
        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
    
    def update(self, form_data):
        dte = self.db.query(DteModel).filter(DteModel.id == form_data.id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        dte.branch_office_id = form_data.branch_office_id
        dte.rut = form_data.rut
        dte.cash_amount = form_data.amount + 5000 if form_data.chip_id == 1 else form_data.amount
        dte.subtotal = round((form_data.amount + 5000)/1.19) if form_data.chip_id == 1 else round((form_data.amount)/1.19)
        dte.tax = (form_data.amount + 5000) - round((form_data.amount + 5000)/1.19) if form_data.chip_id == 1 else form_data.amount - round((form_data.amount)/1.19)
        dte.discount = 0
        dte.total = form_data.amount + 5000 if form_data.chip_id == 1 else form_data.amount
        dte.chip_id = form_data.chip_id
        dte.status_id = 2
        cid = getattr(form_data, "category_id", None)
        if cid is not None:
            dte.category_id = cid
            qty = getattr(form_data, "quantity", None)
            if cid == 3 and qty is not None:
                dte.quantity = int(qty)
            else:
                dte.quantity = None
        else:
            dte.category_id = 1
            dte.quantity = None

        self.db.commit()
        self.db.refresh(dte)
    
    def change_status(self, form_data):
        dte = self.db.query(DteModel).filter(DteModel.id == form_data.id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        dte.expense_type_id = form_data.expense_type_id
        dte.payment_type_id = form_data.payment_type_id
        dte.payment_date = form_data.payment_date
        period = form_data.payment_date.split('-')
        dte.period = period[0] + '-' + period[1]
        dte.comment = form_data.comment
        dte.status_id = 5

        self.db.commit()
        self.db.refresh(dte)

        self.create_account_asset(dte)

    def reject(self, id):
        dte = self.db.query(DteModel).filter(DteModel.id == id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        dte.status_id = 3

        self.db.commit()
        self.db.refresh(dte)

    def get(self, id):
        try:
            data_query = self.db.query(DteModel.id, DteModel.rut, DteModel.branch_office_id, DteModel.total, CustomerModel.address, DteModel.cash_amount, CustomerModel.customer, CustomerModel.region_id, CustomerModel.commune_id, CustomerModel.activity, CustomerModel.email, CustomerModel.phone, DteModel.chip_id, DteModel.folio, DteModel.status_id, DteModel.added_date, BranchOfficeModel.branch_office). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id). \
                        outerjoin(CustomerModel, CustomerModel.rut == DteModel.rut). \
                        filter(DteModel.id == id). \
                        first()

            if data_query:
                # Serializar los datos del empleado
                customer_ticket_data = {
                    "id": data_query.id,
                    "rut": data_query.rut,
                    "branch_office_id": data_query.branch_office_id,
                    "customer": data_query.customer,
                    "email": data_query.email,
                    "phone": data_query.phone,
                    "chip_id": data_query.chip_id,
                    "folio": data_query.folio,
                    "activity": data_query.activity,
                    "region_id": data_query.region_id,
                    "commune_id": data_query.commune_id,
                    "address": data_query.address,
                    "total": data_query.total,
                    "status_id": data_query.status_id,
                    "added_date": data_query.added_date.strftime('%d-%m-%Y') if data_query.added_date else None,
                    "branch_office": data_query.branch_office
                }

                result = {
                    "customer_ticket_data": customer_ticket_data
                }

                serialized_result = json.dumps(result)

                return serialized_result

            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def save_pdf_ticket(self, folio):
        folio = folio
        tipo_dte = 39
        rut_emisor = '76063822'
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        # URL completa
        url = f"https://libredte.cl/api/dte/dte_emitidos/pdf/{tipo_dte}/{folio}/{rut_emisor}?formato=general&papelContinuo=0&copias_tributarias=1&copias_cedibles=1&cedible=0&compress=0&base64=0"

        # Headers con token de autenticación
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {TOKEN}'
        }

        # Realizar la solicitud
        response = requests.get(url, headers=headers)

        # Verificar respuesta
        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
        else:
            # Guardar el PDF en disco
            with open(f'files/{folio}.pdf', 'wb') as f:
                f.write(response.content)
            print(f'PDF guardado como {folio}.pdf')

    def generate(self, form_data):
        expected_total_doc = _ticket_total_from_form(form_data)
        check_dte_existence = self.db.query(DteModel).filter(
            DteModel.branch_office_id == form_data.branch_office_id,
            DteModel.rut == form_data.rut,
            DteModel.total == expected_total_doc,
            DteModel.dte_type_id == 39,
            DteModel.dte_version_id == 1,
            DteModel.status_id == 4,
            DteModel.period == datetime.now().strftime('%Y-%m')
        ).count()

        if check_dte_existence == 0:
            customer = CustomerClass(self.db).get_by_rut(form_data.rut)
            customer_data = json.loads(customer)

            code = self.pre_generate_ticket(customer_data, form_data)
            folio = None

            if code is not None:
                if code == 402:
                    return "LibreDTE payment required"

                folio = self.generate_ticket(customer_data['customer_data']['rut'], code)

                if folio is not None:
                    self.save_pdf_ticket(folio)

            # store() usa status_id=2 (admin/supervisor) o 1 (rol cajero). Borrador folio=0.
            # 1) Match estricto con total; 2) mismo RUT/sucursal/periodo sin total (chip/monto redondeo).
            if folio is not None:
                period_str = datetime.now().strftime("%Y-%m")
                expected_total = expected_total_doc
                rut_clause = _dte_rut_sql_or(DteModel.rut, form_data.rut)

                def _find_draft(require_total: bool):
                    q = (
                        self.db.query(DteModel)
                        .filter(
                            DteModel.branch_office_id == form_data.branch_office_id,
                            rut_clause,
                            DteModel.dte_type_id == 39,
                            DteModel.dte_version_id == 1,
                            DteModel.status_id.in_((1, 2)),
                            DteModel.period == period_str,
                            DteModel.folio == 0,
                        )
                    )
                    if require_total:
                        q = q.filter(DteModel.total == expected_total)
                    return q.order_by(DteModel.id.desc()).first()

                dte = _find_draft(True)
                if dte is None:
                    dte = _find_draft(False)
                if dte is None:
                    dte = (
                        self.db.query(DteModel)
                        .filter(
                            DteModel.branch_office_id == form_data.branch_office_id,
                            rut_clause,
                            DteModel.dte_type_id == 39,
                            DteModel.dte_version_id == 1,
                            DteModel.status_id.in_((1, 2)),
                            DteModel.period == period_str,
                        )
                        .order_by(DteModel.id.desc())
                        .first()
                    )

                if dte:
                    dte.folio = folio
                    dte.status_id = 4
                    _sync_ticket_dte_amounts_from_form(dte, form_data)

                    try:
                        self.db.commit()
                        self.db.refresh(dte)

                        print("Empieza envio de whatsapp")

                        WhatsappClass(self.db).send(dte, form_data.rut)

                        return {"status": "success", "message": "Dte saved successfully"}
                    except Exception as e:
                        self.db.rollback()
                        return {"status": "error", "message": f"Error: {str(e)}"}
                else:
                    return {
                        "status": "error",
                        "message": "Dte not found after generation (no hay borrador tipo 39 para este RUT/monto/sucursal o el total no coincide).",
                    }
            else:
                return {"status": "error", "message": "No se pudo obtener folio desde LibreDTE"}
        else:
            return {"status": "error", "message": "Dte already exists for this RUT in the current period"}
        
    def store(self, form_data, rol_id):
        if form_data.will_save == 1:
            dte = DteModel()

            period = datetime.now().strftime('%Y-%m')

            if rol_id == 1 or rol_id == 2:
                status_id = 2
            elif rol_id == 4:
                status_id = 1
                    
            # Asignar los valores del formulario a la instancia del modelo
            dte.branch_office_id = form_data.branch_office_id
            dte.cashier_id = 0
            dte.dte_type_id = 39
            dte.dte_version_id = 1
            dte.status_id = status_id
            dte.chip_id = form_data.chip_id
            dte.rut = form_data.rut
            dte.folio = 0
            dte.cash_amount = form_data.amount + 5000 if form_data.chip_id == 1 else form_data.amount
            dte.card_amount = 0
            dte.subtotal = round((form_data.amount + 5000)/1.19) if form_data.chip_id == 1 else round((form_data.amount)/1.19)
            dte.tax = (form_data.amount + 5000) - round((form_data.amount + 5000)/1.19) if form_data.chip_id == 1 else form_data.amount - round((form_data.amount)/1.19)
            dte.discount = 0
            dte.total = form_data.amount + 5000 if form_data.chip_id == 1 else form_data.amount
            dte.period = period
            dte.added_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cid = getattr(form_data, "category_id", None)
            dte.category_id = cid if cid is not None else 1
            qty = getattr(form_data, "quantity", None)
            if dte.category_id == 3 and qty is not None:
                dte.quantity = int(qty)
            else:
                dte.quantity = None

            self.db.add(dte)

            try:
                self.db.commit()

                return {"status": "success", "message": "Dte saved successfully"}
            except Exception as e:
                self.db.rollback()
                return {"status": "error", "message": f"Error: {str(e)}"}
        else:
            return 'error'
            
    def create_account_asset(self, form_data):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        if form_data.dte_type_id == 39:
            american_date = form_data.period + '-01'
            utf8_date = HelperClass.convert_to_utf8(american_date)
            expense_type = self.db.query(ExpenseTypeModel).filter(
                ExpenseTypeModel.id == form_data.expense_type_id
            ).first()
            branch_office = self.db.query(BranchOfficeModel).filter(
                BranchOfficeModel.id == form_data.branch_office_id
            ).first()

            gloss = (
                branch_office.branch_office
                + "_"
                + expense_type.accounting_account
                + "_"
                + utf8_date
                + "_BoletaElectronica_"
                + str(form_data.id)
                + "_"
                + str(form_data.folio)
            )
            amount = form_data.total
        
            data = {
                "fecha": american_date,
                "glosa": gloss,
                "detalle": {
                    "debe": {
                        "111000102": amount,
                    },
                    "haber": {
                        expense_type.accounting_account.strip(): round(amount / 1.19),
                        "221000226": round(amount - (amount / 1.19)),
                    }
                },
                "operacion": "I",
                "documentos": {
                    "emitidos": [
                        {
                            "dte": form_data.dte_type_id,
                            "folio": form_data.folio,
                        }
                    ]
                },
            }
        else:
            american_date = form_data.period + '-01'
            utf8_date = HelperClass.convert_to_utf8(american_date)
            expense_type = self.db.query(ExpenseTypeModel).filter(
                ExpenseTypeModel.id == form_data.expense_type_id
            ).first()
            branch_office = self.db.query(BranchOfficeModel).filter(
                BranchOfficeModel.id == form_data.branch_office_id
            ).first()

            gloss = (
                branch_office.branch_office
                + "_"
                + expense_type.accounting_account
                + "_"
                + utf8_date
                + "_NotaCredito_"
                + str(form_data.id)
                + "_"
                + str(form_data.folio)
            )
            amount = form_data.total
        
            data = {
                "fecha": american_date,
                "glosa": gloss,
                "detalle": {
                    "debe": {
                        expense_type.accounting_account.strip(): round(amount / 1.19),
                        "221000226": round(amount - (amount / 1.19)),
                    },
                    "haber": {
                        "111000102": amount,
                    }
                },
                "operacion": "I",
                "documentos": {
                    "emitidos": [
                        {
                            "dte": form_data.dte_type_id,
                            "folio": form_data.folio,
                        }
                    ]
                },
            }

        try:
            url = f"https://libredte.cl/api/lce/lce_asientos/crear/" + "76063822"

            response = requests.post(
                url,
                json=data,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 200:
                return "Accounting entry created successfully"
            else:
                return f"Accounting entry creation failed."

        except Exception as e:
            print("Error al conectarse a la API:", e)
            return None
    
    def store_credit_note(self, form_data):
        dte = self.db.query(DteModel).filter(DteModel.id == form_data.id).first()
        
        customer = CustomerClass(self.db).get_by_rut(dte.rut)
        customer_data = json.loads(customer)

        dte_date = self.get_dte_date(dte.folio)

        code = self.pre_generate_credit_note_ticket(customer_data, dte.folio, dte.cash_amount, dte_date)

        folio = None

        if code is not None:
            if code == 402:
                return "LibreDTE payment required"

            folio = self.generate_credit_note_ticket(customer_data['customer_data']['rut'], code)

        if folio != None:
            dte.status_id = 5
            dte.reason_id = form_data.reason_id
            dte.comment = 'Código de autorización: Nota de Crédito ' + str(code)
            self.db.add(dte)
            self.db.commit()

            credit_note_dte = DteModel()
                    
            # Asignar los valores del formulario a la instancia del modelo
            credit_note_dte.branch_office_id = dte.branch_office_id
            credit_note_dte.cashier_id = dte.cashier_id
            credit_note_dte.dte_type_id = 61
            credit_note_dte.dte_version_id = 1
            credit_note_dte.status_id = 5
            credit_note_dte.chip_id = 0
            credit_note_dte.rut = customer_data['customer_data']['rut']
            credit_note_dte.folio = folio
            credit_note_dte.cash_amount = dte.cash_amount
            credit_note_dte.card_amount = 0
            credit_note_dte.subtotal = round(dte.cash_amount/1.19)
            credit_note_dte.tax = (dte.cash_amount) - round((dte.cash_amount)/1.19)
            credit_note_dte.discount = 0
            credit_note_dte.total = dte.cash_amount
            credit_note_dte.added_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            credit_note_dte.category_id = 1
            credit_note_dte.quantity = None

            self.db.add(credit_note_dte)
            
            try:
                self.db.commit()

                return {"status": "success", "message": "Credit Note saved successfully"}
            except Exception as e:
                self.db.rollback()
                return {"status": "error", "message": f"Error: {str(e)}"}
        else:
            return "Creditnote was not created"
        
    def pre_generate_ticket(self, customer_data, form_data):  # Added self as the first argument
        branch_office_data = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == form_data.branch_office_id).first()

        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        category_id = getattr(form_data, "category_id", None) or 1
        qty = getattr(form_data, "quantity", None)

        if category_id == 3 and qty is not None and int(qty) >= 1:
            q = int(qty)
            unit_price = round(int(form_data.amount) / q)
            data = {
                "Encabezado": {
                    "IdDoc": {
                        "TipoDTE": 39
                    },
                    "Emisor": {
                        "RUTEmisor": "76063822-6",
                        'CdgSIISucur': branch_office_data.dte_code,
                    },
                    "Receptor": {
                        "RUTRecep": customer_data['customer_data']['rut'],
                        "RznSocRecep": customer_data['customer_data']['customer'],
                        "GiroRecep": customer_data['customer_data']['activity'],
                        "DirRecep": customer_data['customer_data']['region'],
                        "CmnaRecep": customer_data['customer_data']['commune'],
                        'Contacto': customer_data['customer_data']['email'],
                        'CorreoRecep': customer_data['customer_data']['email'],
                    }
                },
                "Detalle": [
                    {
                        "NmbItem": " Prestación de estacionamientos. Fecha:" + datetime.now().strftime('%d-%m-%Y'),
                        "QtyItem": q,
                        "PrcItem": unit_price,
                    }
                ]
            }
        elif form_data.chip_id == 1:
            if form_data.will_save == 0 or form_data.will_save == None or form_data.will_save == "":
                amount = form_data.amount - 5000
            else:
                amount = form_data.amount

            data = {
                "Encabezado": {
                    "IdDoc": {
                        "TipoDTE": 39
                    },
                    "Emisor": {
                        "RUTEmisor": "76063822-6",
                        'CdgSIISucur': branch_office_data.dte_code,
                    },
                    "Receptor": {
                        "RUTRecep": customer_data['customer_data']['rut'],
                        "RznSocRecep": customer_data['customer_data']['customer'],
                        "GiroRecep": customer_data['customer_data']['activity'],
                        "DirRecep": customer_data['customer_data']['region'],
                        "CmnaRecep": customer_data['customer_data']['commune'],
                        'Contacto': customer_data['customer_data']['email'],
                        'CorreoRecep': customer_data['customer_data']['email'],
                    }
                },
                "Detalle": [
                    {
                        "NmbItem": " Prestación de estacionamientos. Fecha:" + datetime.now().strftime('%d-%m-%Y'),
                        "QtyItem": 1,
                        "PrcItem": amount,
                    },
                    {
                        "NmbItem": "Chip",
                        "QtyItem": 1,
                        "PrcItem": 5000,
                    },
                ]
            }
        else:
            data = {
                "Encabezado": {
                    "IdDoc": {
                        "TipoDTE": 39
                    },
                    "Emisor": {
                        "RUTEmisor": "76063822-6",
                        'CdgSIISucur': branch_office_data.dte_code,
                    },
                    "Receptor": {
                        "RUTRecep": customer_data['customer_data']['rut'],
                        "RznSocRecep": customer_data['customer_data']['customer'],
                        "GiroRecep": customer_data['customer_data']['activity'],
                        "DirRecep": customer_data['customer_data']['region'],
                        "CmnaRecep": customer_data['customer_data']['commune'],
                        'Contacto': customer_data['customer_data']['email'],
                        'CorreoRecep': customer_data['customer_data']['email'],
                    }
                },
                "Detalle": [
                    {
                        "NmbItem": " Prestación de estacionamientos. Fecha:" + datetime.now().strftime('%d-%m-%Y'),
                        "QtyItem": 1,
                        "PrcItem": form_data.amount,
                    }
                ]
            }

        try:
            # Endpoint para generar un DTE temporal
            url = f"https://libredte.cl/api/dte/documentos/emitir?normalizar=1&formato=json&links=0&email=0"
            
            # Enviar solicitud a la API
            response = requests.post(
                url,
                json=data,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )
            
            # Manejar la respuesta
            if response.status_code == 200:
                dte_data = response.json()
                code = dte_data.get("codigo")

                return code
            else:
                return response.status_code

        except Exception as e:
            print("Error al conectarse a la API:", e)
            return None
    
    def get_dte_date(self, folio):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        # Endpoint para generar un DTE temporal
        url = f"https://libredte.cl/api/dte/dte_emitidos/info/39/" + str(folio) + '/76063822?getXML=0&getDetalle=0&getDatosDte=0&getTed=0&getResolucion=0&getEmailEnviados=0&getLinks=0&getReceptor=0&getSucursal=0&getUsuario=0'
            
        # Enviar solicitud a la API
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
            },
        )

        response_data = response.json()

        return response_data['fecha']

    def pre_generate_credit_note_ticket(self, customer_data, folio, cash_amount, added_date):  # Added self as the first argument
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        amount = round(cash_amount/1.19)

        data = {
                "Encabezado": {
                    "IdDoc": {
                        "TipoDTE": "61",
                        "Folio": 0,
                        "FchEmis": added_date,
                        "TpoTranVenta": 1,
                        "FmaPago": "1",
                    },
                    "Emisor": {
                        "RUTEmisor": "76063822-6"
                    },
                    "Receptor": {
                        "RUTRecep": customer_data['customer_data']['rut'],
                        "RznSocRecep": customer_data['customer_data']['customer'],
                        "GiroRecep": customer_data['customer_data']['activity'],
                        "DirRecep": customer_data['customer_data']['region'],
                        "CmnaRecep": customer_data['customer_data']['commune'],
                    }
                },
                "Detalle": [
                    {
                        "NmbItem": "Nota de Crédito de Venta",
                        "QtyItem": 1,
                        "PrcItem": amount,
                        "MontoItem": amount,
                    }
                ],
                "Referencia": [ {
                    "TpoDocRef": 39,
                    "FolioRef": folio,
                    "FchRef": added_date,
                    "CodRef": 1,
                    "RazonRef": "Anula factura o boleta"
                }],
            }

        try:
            # Endpoint para generar un DTE temporal
            url = f"https://libredte.cl/api/dte/documentos/emitir?normalizar=1&formato=json&links=0&email=0"
            
            # Enviar solicitud a la API
            response = requests.post(
                url,
                json=data,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )
            
            # Manejar la respuesta
            if response.status_code == 200:
                dte_data = response.json()
                code = dte_data.get("codigo")

                return code
            else:
                return response.status_code

        except Exception as e:
            print("Error al conectarse a la API:", e)
            return None
        
    def generate_ticket(self, customer_rut, code):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        data = {
            "emisor": "76063822-6",
            "receptor": customer_rut,
            "dte": 39,
            "codigo": code
        }
            
        try:
            # Endpoint para generar un DTE temporal
            url = f"https://libredte.cl/api/dte/documentos/generar?getXML=0&links=0&email=1&retry=1&gzip=0"
            
            # Enviar solicitud a la API
            response = requests.post(
                url,
                json=data,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )
            
            if response.status_code == 200:
                dte_data = response.json()
                folio = dte_data.get("folio")

                return folio
            else:
                print("Error al generar el DTE:")
                print(response.status_code, response.json())
                return None

        except Exception as e:
            print("Error al conectarse a la API:", e)
            return None

    def generate_credit_note_ticket(self, customer_rut, code):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        data = {
            "emisor": "76063822-6",
            "receptor": customer_rut,
            "dte": 61,
            "codigo": code
        }

        try:
            # Endpoint para generar un DTE temporal
            url = f"https://libredte.cl/api/dte/documentos/generar?getXML=0&links=0&email=1&retry=1&gzip=0"
            
            # Enviar solicitud a la API
            response = requests.post(
                url,
                json=data,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )
            
            # Manejar la respuesta
            print(response)

            if response.status_code == 200:
                dte_data = response.json()
                folio = dte_data.get("folio")

                return folio
            else:
                print("Error al generar el DTE:")
                print(response.status_code, response.json())
                return None

        except Exception as e:
            print("Error al conectarse a la API:", e)
            return None
        
    def download(self, id):
        dte = self.db.query(DteModel).filter(DteModel.id == id).first()

        if dte:
            TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

            # Endpoint para generar un DTE temporal
            url = f"https://libredte.cl/api/dte/dte_emitidos/pdf/39/"+ str(dte.folio) +"/76063822-6?formato=general&papelContinuo=0&copias_tributarias=1&copias_cedibles=1&cedible=0&compress=0&base64=0"

            # Enviar solicitud a la API
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )

            # Manejar la respuesta
            if response.status_code == 200:
                pdf_content = response.content
                timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                unique_id = uuid.uuid4().hex[:8]  # 8 caracteres únicos
                unique_filename = f"{timestamp}_{unique_id}.pdf"

                # Ruta remota en Azure
                remote_path = f"{unique_filename}"  # Organizar archivos en una carpeta específica

                self.file_class.temporal_upload(pdf_content, remote_path)  # Llamada correcta

                # Descargar archivo desde Azure File Share
                file_contents = self.file_class.download(remote_path)

                # Convertir el contenido del archivo a base64
                encoded_file = base64.b64encode(file_contents).decode('utf-8')

                self.file_class.delete(remote_path)  # Llamada correcta

                # Retornar el nombre del archivo y su contenido como base64
                return {
                    "file_name": unique_filename,
                    "file_data": encoded_file
                }
            else:
                return None
            
    def verify(self, id):
        dte = self.db.query(DteModel).filter(DteModel.id == id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        # Actualizar campos
        dte.status_id = 2
        self.db.commit()
        self.db.refresh(dte)
    
    def pre_accept(self, id):
        dte = self.db.query(DteModel).filter(DteModel.id == id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Dte no encontrado")

        # Actualizar campos
        dte.status_id = 2
        self.db.commit()
        self.db.refresh(dte)

    def check_payments(self):
        dtes = self.db.query(DteModel).filter(DteModel.status_id == 4).filter(DteModel.dte_type_id  == 39).filter(DteModel.dte_version_id == 1).all()

        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        for dte in dtes:
            print(f"Verificando DTE tipo 39 folio: {dte.folio}")

            url = f"https://libredte.cl/api/dte/dte_emitidos/cobro/39/{dte.folio}/76063822?getDocumento=0&getDetalle=0&getLinks=0"
                
            response = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                },
            )
            print(response.text)

            if response.status_code == 200:
                data = json.loads(response.text)
                print(data)

                payment_status = data.get("pagado")
                payment_date = data.get("pagado")
                amount = data.get("total")
                datos_json = data.get("datos")

                # Verificar si está pagado - puede venir como None, null, "none", "null", o string vacío
                is_paid = False
                if payment_status is not None and payment_status != "" and str(payment_status).lower() not in ["none", "null"]:
                    is_paid = True

                if is_paid:
                    print('DTE está pagado. Procesando...')
                    
                    # Extraer authorizationCode de datos JSON
                    authorization_code = None
                    if datos_json:
                        try:
                            datos_dict = json.loads(datos_json)
                            detail_output = datos_dict.get("detailOutput", {})
                            authorization_code = detail_output.get("authorizationCode")
                        except:
                            pass

                    if dte.status_id == 4:
                        print('Actualizando DTE...')
                        dte.expense_type_id = 25
                        dte.payment_type_id = 2
                        dte.card_amount = amount
                        dte.payment_date = payment_date
                        dte.status_id = 5
                        dte.updated_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                        
                        if authorization_code:
                            dte.comment = f"Código de autorización: {authorization_code}"

                        self.db.commit()
                        self.db.refresh(dte)

                        print(f"Dte actualizado correctamente: {dte.folio}")

                        WhatsappClass(self.db).notify_payment(dte.folio)


