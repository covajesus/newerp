import requests
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import desc, cast, Date, func, or_
from sqlalchemy.dialects import mysql
from app.backend.db.models import DteModel, BranchOfficeModel, CustomerModel, SupplierModel, CommuneModel, TotalDtesToBeSentModel
from app.backend.classes.helper_class import HelperClass
from app.backend.classes.customer_class import CustomerClass
from app.backend.classes.whatsapp_class import WhatsappClass
from app.backend.classes.customer_ticket_class import CustomerTicketClass
from app.backend.classes.customer_bill_class import CustomerBillClass
from app.backend.classes.customer_ticket_bill_class import CustomerTicketBillClass


# Clases auxiliares para simulación de datos de formulario
class FormDataSimulator:
    def __init__(self, dte):
        self.branch_office_id = dte.branch_office_id
        self.rut = dte.rut
        self.amount = dte.cash_amount if dte.chip_id != 1 else dte.cash_amount - 5000
        self.chip_id = dte.chip_id
        self.will_save = 0  # No guardar, solo generar
        self.id = dte.id  # Necesario para customer_bill_class

class CreditNoteFormDataSimulator:
    def __init__(self, dte_id, reason_id=1):
        self.id = dte_id
        self.reason_id = reason_id

class DteClass:
    def __init__(self, db):
        self.db = db

    def validate_old_dte(self, folio, rut, dte_version_id):
        try:
            folio_count = self.db.query(DteModel).filter(DteModel.folio == folio).filter(DteModel.rut == rut).filter(DteModel.dte_version_id == dte_version_id).count()
            
            if folio_count > 1:
                return 1  # Retorna 1 si hay menos de 100 folios
            else:
                return 0  # Retorna 0 si hay 100 o más folios
        
        except Exception as e:
            # Captura cualquier error y retorna el mensaje de error
            error_message = str(e)
            return f"Error: {error_message}"

    def get_old_dtes(self):
        try:
            # Construir la consulta base con los filtros aplicados
            query = self.db.query(
                DteModel.id, 
                DteModel.branch_office_id, 
                DteModel.folio, 
                DteModel.total, 
                DteModel.entrance_hour,
                DteModel.exit_hour,
                DteModel.added_date,
                BranchOfficeModel.branch_office
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
            ).filter(
                *filters
            ).order_by(
                desc(DteModel.added_date),
                desc(DteModel.entrance_hour),
                desc(DteModel.exit_hour)
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
                    "branch_office_id": dte.branch_office_id,
                    "folio": dte.folio,
                    "total": dte.total,
                    "entrance_hour": dte.entrance_hour,
                    "exit_hour": dte.exit_hour,
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
                    "branch_office_id": dte.branch_office_id,
                    "folio": dte.folio,
                    "total": dte.total,
                    "entrance_hour": dte.entrance_hour,
                    "exit_hour": dte.exit_hour,
                    "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                    "branch_office": dte.branch_office
                } for dte in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}


    def get_all(self, folio=None, branch_office_id=None, rut=None, customer=None, since=None, until=None, amount=None, supervisor_id=None, status_id=None, page=0, items_per_page=10):
        try:
            # Inicialización de filtros dinámicos
            filters = []
            if folio is not None:
                filters.append(DteModel.folio == folio) 
            if branch_office_id is not None:
                filters.append(DteModel.branch_office_id == branch_office_id)
            if rut is not None:
                filters.append(DteModel.rut == rut)
            if customer is not None:
                filters.append(DteModel.customer.like(f"%{customer}%"))
            if until is not None:
                filters.append(DteModel.added_date >= until)  # Fecha desde
            if since is not None:
                filters.append(DteModel.added_date <= since)  # Fecha hasta
            if amount is not None:
                filters.append(DteModel.total == amount)
            if supervisor_id is not None:
                filters.append(DteModel.supervisor_id == supervisor_id)
            if status_id is not None:
                filters.append(DteModel.status_id == status_id)

            # Construir la consulta base con los filtros aplicados
            query = self.db.query(
                DteModel.id, 
                DteModel.branch_office_id, 
                DteModel.folio, 
                DteModel.total, 
                DteModel.entrance_hour,
                DteModel.exit_hour,
                DteModel.added_date,
                BranchOfficeModel.branch_office
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
            ).filter(
                *filters
            ).order_by(
                desc(DteModel.added_date),
                desc(DteModel.entrance_hour),
                desc(DteModel.exit_hour)
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
                    "branch_office_id": dte.branch_office_id,
                    "folio": dte.folio,
                    "total": dte.total,
                    "entrance_hour": dte.entrance_hour,
                    "exit_hour": dte.exit_hour,
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
                    "branch_office_id": dte.branch_office_id,
                    "folio": dte.folio,
                    "total": dte.total,
                    "entrance_hour": dte.entrance_hour,
                    "exit_hour": dte.exit_hour,
                    "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                    "branch_office": dte.branch_office
                } for dte in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}

    def get_all_with_customer(
        self,
        rol_id,
        supervisor_rut,
        folio=None,
        branch_office_id=None,
        rut=None,
        customer=None,
        period=None,
        amount=None,
        supervisor_id=None,
        status_id=None,
        dte_version_id=None,
        page=0,
        items_per_page=10
    ):
        try:
            if rol_id == 1 or rol_id == 2:
                # Filtros dinámicos
                filters = []
                if folio:
                    filters.append(DteModel.folio == folio)
                if branch_office_id:
                    filters.append(DteModel.branch_office_id == branch_office_id)
                if rut:
                    filters.append(DteModel.rut == rut)
                if customer:
                    filters.append(CustomerModel.customer.like(f"%{customer}%"))
                if period:
                    filters.append(DteModel.period == period)
                if amount:
                    filters.append(DteModel.total == amount)
                if supervisor_id:
                    filters.append(DteModel.supervisor_id == supervisor_id)
                if status_id:
                    filters.append(DteModel.status_id == status_id)

                filters.append(DteModel.rut != None)

                if dte_version_id is not None:
                    filters.append(DteModel.dte_version_id == dte_version_id)

                # Condición fija: status_id IN (4, 5)
                filters.append(DteModel.status_id.in_([4, 5]))

                # Construcción de la consulta
                query = self.db.query(
                    DteModel.id,
                    DteModel.branch_office_id,
                    DteModel.folio,
                    DteModel.total,
                    DteModel.entrance_hour,
                    DteModel.exit_hour,
                    DteModel.status_id,
                    DteModel.payment_date,
                    CustomerModel.rut,
                    CustomerModel.customer,
                    DteModel.dte_type_id,
                    DteModel.added_date,
                    BranchOfficeModel.branch_office
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
                ).outerjoin(
                    CustomerModel, CustomerModel.rut == DteModel.rut
                ).filter(
                    *filters
                ).order_by(
                    DteModel.id.desc()
                )
            elif rol_id == 4:
                # Filtros dinámicos
                filters = []
                if folio:
                    filters.append(DteModel.folio == folio)
                if branch_office_id:
                    filters.append(DteModel.branch_office_id == branch_office_id)
                if rut:
                    filters.append(DteModel.rut == rut)
                if customer:
                    filters.append(CustomerModel.customer.like(f"%{customer}%"))
                if period:
                    filters.append(DteModel.period == period)
                if amount:
                    filters.append(DteModel.total == amount)
                if supervisor_id:
                    filters.append(DteModel.supervisor_id == supervisor_id)
                if status_id:
                    filters.append(DteModel.status_id == status_id)

                filters.append(DteModel.rut != None)

                if dte_version_id is not None:
                    filters.append(DteModel.dte_version_id == dte_version_id)

                # Condición fija: status_id IN (4, 5)
                filters.append(DteModel.status_id.in_([4, 5]))

                # Construcción de la consulta
                query = self.db.query(
                    DteModel.id,
                    DteModel.branch_office_id,
                    DteModel.folio,
                    DteModel.total,
                    DteModel.entrance_hour,
                    DteModel.exit_hour,
                    DteModel.status_id,
                    DteModel.payment_date,
                    CustomerModel.rut,
                    CustomerModel.customer,
                    DteModel.dte_type_id,
                    DteModel.added_date,
                    BranchOfficeModel.branch_office
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
                ).outerjoin(
                    CustomerModel, CustomerModel.rut == DteModel.rut
                ).filter(
                    *filters
                ).filter(
                    BranchOfficeModel.principal_supervisor == supervisor_rut
                ).order_by(
                    DteModel.id.desc()
                )

            # Paginación
            total_items = query.count()

            if total_items == 0:
                return {
                    "status": "ok",
                    "message": "No data found",
                    "data": [],
                    "total_items": 0,
                    "total_pages": 0,
                    "current_page": page,
                }

            total_pages = (total_items + items_per_page - 1) // items_per_page

            if page < 1 or page > total_pages:
                return {"status": "error", "message": "Invalid page number"}

            offset = (page - 1) * items_per_page
            data = query.offset(offset).limit(items_per_page).all()

            # Mostrar consulta generada
            print(query.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))

            # Mostrar rango de elementos
            start_item = offset + 1
            end_item = min(offset + items_per_page, total_items)
            print(f"Mostrando resultados del {start_item} al {end_item} de {total_items}")

            # Serializar resultados
            serialized_data = [{
                "id": dte.id,
                "branch_office_id": dte.branch_office_id,
                "folio": dte.folio,
                "dte_type_id": dte.dte_type_id,
                "total": dte.total,
                "customer": dte.customer,
                "rut": dte.rut,
                "entrance_hour": dte.entrance_hour,
                "payment_date": dte.payment_date,
                "status_id": dte.status_id,
                "exit_hour": dte.exit_hour,
                "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                "branch_office": dte.branch_office
            } for dte in data]

            return {
                "status": "ok",
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "items_per_page": items_per_page,
                "from_item": start_item,
                "to_item": end_item,
                "data": serialized_data
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}


    def get_all_with_customer_to_review(
        self,
        folio=None,
        branch_office_id=None,
        rut=None,
        customer=None,
        period=None,
        amount=None,
        supervisor_id=None,
        status_id=None,
        dte_version_id=None,
        page=0,
        items_per_page=10
    ):
        try:
            # Filtros dinámicos
            filters = []
            if folio:
                filters.append(DteModel.folio == folio)
            if branch_office_id:
                filters.append(DteModel.branch_office_id == branch_office_id)
            if rut:
                filters.append(DteModel.rut == rut)
            if customer:
                filters.append(CustomerModel.customer.like(f"%{customer}%"))
            if period:
                filters.append(DteModel.period == period)
            if amount:
                filters.append(DteModel.total == amount)
            if supervisor_id:
                filters.append(DteModel.supervisor_id == supervisor_id)
            if status_id:
                filters.append(DteModel.status_id == status_id)

            filters.append(DteModel.rut != None)

            if dte_version_id is not None:
                filters.append(DteModel.dte_version_id == dte_version_id)

            # Condición fija: status_id IN (4, 5)
            filters.append(DteModel.status_id.in_([16]))

            # Construcción de la consulta
            query = self.db.query(
                DteModel.id,
                DteModel.branch_office_id,
                DteModel.folio,
                DteModel.total,
                DteModel.entrance_hour,
                DteModel.exit_hour,
                DteModel.status_id,
                DteModel.payment_date,
                CustomerModel.rut,
                CustomerModel.customer,
                DteModel.dte_type_id,
                DteModel.added_date,
                BranchOfficeModel.branch_office
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
            ).outerjoin(
                CustomerModel, CustomerModel.rut == DteModel.rut
            ).filter(
                *filters
            ).order_by(
                DteModel.id.desc()
            )

            # Paginación
            total_items = query.count()

            if total_items == 0:
                return {
                    "status": "ok",
                    "message": "No data found",
                    "data": [],
                    "total_items": 0,
                    "total_pages": 0,
                    "current_page": page,
                }

            total_pages = (total_items + items_per_page - 1) // items_per_page

            if page < 1 or page > total_pages:
                return {"status": "error", "message": "Invalid page number"}

            offset = (page - 1) * items_per_page
            data = query.offset(offset).limit(items_per_page).all()

            # Mostrar consulta generada
            print(query.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))

            # Mostrar rango de elementos
            start_item = offset + 1
            end_item = min(offset + items_per_page, total_items)
            print(f"Mostrando resultados del {start_item} al {end_item} de {total_items}")

            # Serializar resultados
            serialized_data = [{
                "id": dte.id,
                "branch_office_id": dte.branch_office_id,
                "folio": dte.folio,
                "dte_type_id": dte.dte_type_id,
                "total": dte.total,
                "customer": dte.customer,
                "rut": dte.rut,
                "entrance_hour": dte.entrance_hour,
                "payment_date": dte.payment_date,
                "status_id": dte.status_id,
                "exit_hour": dte.exit_hour,
                "added_date": dte.added_date.strftime('%d-%m-%Y') if dte.added_date else None,
                "branch_office": dte.branch_office
            } for dte in data]

            return {
                "status": "ok",
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "items_per_page": items_per_page,
                "from_item": start_item,
                "to_item": end_item,
                "data": serialized_data
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}
        
    def upload_deposit_transfer(self, form_data, support):
        # Crear una nueva instancia de ContractModel
        dte = self.db.query(DteModel).filter(DteModel.id == form_data.dte_id).first()
        dte.status_id = 16
        dte.payment_type_id = form_data.payment_type_id
        dte.payment_amount = form_data.deposited_amount
        dte.payment_number = form_data.payment_number
        dte.payment_date = form_data.deposit_date
        dte.support = support

        try:
            self.db.commit()
            self.db.refresh(dte)
            return {"status": "success", "message": "Dte updated successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def get_received_tributary_documents(self, folio=None, branch_office_id=None, rut=None, supplier=None, since=None, until=None, amount=None, supervisor_id=None, status_id=None, dte_type_id=None, dte_version_id=None, page=0, items_per_page=10):
        try:
            # Inicialización de filtros dinámicos
            print(folio, branch_office_id, rut, supplier, until, since, amount, supervisor_id, status_id)
            filters = []
            if folio is not None:
                filters.append(DteModel.folio == folio) 
            if branch_office_id is not None:
                filters.append(DteModel.branch_office_id == branch_office_id)
            if rut is not None:
                filters.append(DteModel.rut == rut)
            if supplier is not None:
                filters.append(SupplierModel.supplier.like(f"%{supplier}%"))
            if until is not None:
                filters.append(DteModel.added_date <= until)
            if since is not None:
                filters.append(DteModel.added_date >= since)
            if amount is not None:
                filters.append(DteModel.total == amount)
            if supervisor_id is not None:
                filters.append(DteModel.supervisor_id == supervisor_id)
            if status_id is not None:
                filters.append(DteModel.status_id == status_id)

            filters.append(DteModel.rut != None)
            filters.append(DteModel.dte_version_id == dte_version_id)

            # Construir la consulta base con los filtros aplicados
            query = self.db.query(
                DteModel.id, 
                DteModel.branch_office_id, 
                DteModel.folio, 
                DteModel.total, 
                DteModel.entrance_hour,
                DteModel.exit_hour,
                DteModel.status_id,
                SupplierModel.rut,
                SupplierModel.supplier,
                DteModel.added_date,
                BranchOfficeModel.branch_office
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == DteModel.branch_office_id
            ).outerjoin(
                SupplierModel, SupplierModel.rut == DteModel.rut
            ).filter(
                *filters
            ).order_by(
                DteModel.id.desc()
            )

            # Paginación
            total_items = query.count()

            if total_items == 0:
                return {
                    "status": "ok",
                    "message": "No data found",
                    "data": [],
                    "total_items": 0,
                    "total_pages": 0,
                    "current_page": page,
                }

            total_pages = (total_items + items_per_page - 1) // items_per_page

            if page < 1 or page > total_pages:
                return {"status": "error", "message": "Invalid page number"}

            offset = (page - 1) * items_per_page
            data = query.offset(offset).limit(items_per_page).all()

            # Mostrar consulta generada
            print(query.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))

            # Mostrar rango de elementos
            start_item = offset + 1
            end_item = min(offset + items_per_page, total_items)
            print(f"Mostrando resultados del {start_item} al {end_item} de {total_items}")


            # Serializar los resultados
            serialized_data = [{
                "id": dte.id,
                "branch_office_id": dte.branch_office_id,
                "folio": dte.folio,
                "total": dte.total,
                "supplier": dte.supplier,
                "rut": dte.rut,
                "entrance_hour": dte.entrance_hour,
                "status_id": dte.status_id,
                "exit_hour": dte.exit_hour,
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

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}

    def import_by_rut(self, rut):
        url = "https://libredte.cl/api/dte/dte_emitidos/buscar/76063822"
        token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        # Calcular fecha desde 2 meses atrás
        two_months_ago = datetime.now() - relativedelta(months=2)
        since_date = two_months_ago.strftime("%Y-%m-01")

        payload = json.dumps({
            "receptor": rut,
            "fecha_desde": since_date
        })

        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        print(payload)

        response = requests.post(url, headers=headers, data=payload)

        try:
            data = response.json()
            print("Respuesta recibida:", data)

            # Si la respuesta es una lista directamente
            if isinstance(data, list):
                dtes = data
            # Si la respuesta es un dict con clave "dtes"
            elif isinstance(data, dict) and "dtes" in data:
                dtes = data["dtes"]
            else:
                print("No se encontraron documentos o formato inesperado.")
                return

            if not dtes:
                print("No se encontraron documentos para ese RUT.")
                return

            print(f"Se encontraron {len(dtes)} documentos para el RUT {rut}:\n")
            for dte in dtes:
                customer = self.db.query(CustomerModel).filter(CustomerModel.rut == rut).first()

                if not customer:
                    url = "https://libredte.cl/api/dte/contribuyentes/info/" + str(rut)

                    payload={}

                    response = requests.request("GET", url, headers=headers, data=payload)

                    print(response.text)

                    data = response.json()
                    print("Información del contribuyente:")
                    print(f"RUT: {data.get('rut')}-{data.get('dv')}")
                    print(f"Razón Social: {data.get('razon_social')}")
                    print(f"Giro: {data.get('giro')}")
                    print(f"Actividad Económica: {data.get('actividad_economica')}")
                    print(f"Teléfono: {data.get('telefono')}")
                    print(f"Email: {data.get('email')}")
                    print(f"Dirección: {data.get('direccion')}")
                    print(f"Comuna: {data.get('comuna')} ({data.get('comuna_glosa')})")
                    print(f"Última Modificación: {data.get('modificado')}")

                    raw_phone = data.get("telefono", "")
                    cleaned_phone = raw_phone.replace("+56", "").replace(" ", "").strip()

                    commune_data = self.db.query(CommuneModel).filter(
                                    func.lower(CommuneModel.commune).like(f"%{data.get('comuna_glosa', '').lower()}%")
                                ).first()
            
                    store_customer = CustomerModel(
                        rut=rut,
                        region_id=commune_data.region_id,
                        commune_id=commune_data.id,
                        customer=data.get('razon_social'),
                        address=data.get('direccion'),
                        activity=data.get('giro', ''),
                        phone=cleaned_phone,
                        email=data.get('email'),
                        added_date=datetime.now()
                    )

                    self.db.add(store_customer)

                    try:
                        self.db.commit()
                        print(f"Cliente {dte.get('razon_social', 'Cliente Desconocido')} guardado correctamente.")
                    except Exception as e:
                        error_message = str(e)
                        print(f"Error al guardar el cliente {dte.get('razon_social', 'Cliente Desconocido')}: {error_message}")

                print(f"""
                    Tipo: {dte.get('tipo')}
                    Folio: {dte.get('folio')}
                    Razón Social: {dte.get('razon_social')}
                    Fecha: {dte.get('fecha')}
                    Total: {dte.get('total')}
                    Estado: {dte.get('estado')}
                    Track ID: {dte.get('track_id')}
                    Usuario: {dte.get('usuario')}
                    ¿Tiene XML?: {"Sí" if dte.get("has_xml") else "No"}
                    -----------------------------
                                    """)

                dte_qty = self.db.query(DteModel).filter(DteModel.folio == dte.get('folio')).filter(DteModel.dte_version_id == 1).count()

                if dte_qty == 0:
                    if dte.get('tipo') == 'Factura electrónica':
                        dte_type_id = 33
                    elif dte.get('tipo') == 'Boleta electrónica':
                        dte_type_id = 39
                    elif dte.get('tipo') == 'Nota de crédito electrónica':
                        dte_type_id = 61
                    
                    branch_office = self.db.query(BranchOfficeModel).filter(
                            BranchOfficeModel.dte_code == dte.get('sucursal_sii')
                        ).first()

                    validate_dte_existence = self.db.query(DteModel).filter(
                            DteModel.rut == rut,
                            DteModel.dte_type_id == dte_type_id,
                            DteModel.dte_version_id == 1,
                            DteModel.period == datetime.now().strftime('%Y-%m'),
                            DteModel.folio == dte.get('folio'),
                        ).count()

                    branch_office_qty = self.db.query(BranchOfficeModel).filter(
                            BranchOfficeModel.dte_code == dte.get('sucursal_sii')
                        ).count()
        
                    if validate_dte_existence == 0 and branch_office_qty > 0:
                        store_dte = DteModel(
                            branch_office_id=branch_office.id,
                            cashier_id=0,
                            dte_type_id=dte_type_id,
                            dte_version_id=1,
                            status_id=4,
                            folio=dte.get('folio'),
                            rut=rut,
                            cash_amount=dte.get('total'),
                            card_amount=0,
                            subtotal=round(dte.get('total')/1.19),
                            tax=dte.get('total') - round(dte.get('total')/1.19),
                            discount=0,
                            total=dte.get('total'),
                            ticket_serial_number=0,
                            ticket_hour=0,
                            ticket_transaction_number=0,
                            ticket_dispenser_number=0,
                            ticket_number=0,
                            ticket_station_number=0,
                            ticket_sa=0,
                            ticket_correlative=0,
                            entrance_hour='',
                            exit_hour='',
                            period=datetime.now().strftime('%Y-%m'),
                            added_date=dte.get('fecha')
                        )

                        self.db.add(store_dte)

                    try:
                        self.db.commit()
                        print(f"DTE con folio {dte.get('folio')} guardado correctamente.")
                    except Exception as e:
                        error_message = str(e)
                        print(f"Error al guardar el DTE con folio {dte.get('folio')}: {error_message}")
                else:
                    print(f"El DTE con folio {dte.get('folio')} ya existe en la base de datos.")

        except json.JSONDecodeError:
            print("La respuesta no es un JSON válido:")
            print(response.text)

    def refresh_import_by_rut(self):
        customers = self.db.query(CustomerModel).filter(CustomerModel.rut != '66666666-6').all()
        for customer in customers:
            print(customer.rut)
            rut = customer.rut
            url = "https://libredte.cl/api/dte/dte_emitidos/buscar/76063822"
            token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

            payload = json.dumps({
                "receptor": rut,
                "fecha_desde": datetime.now().strftime("%Y-%m-01")
            })

            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {token}'
            }

            response = requests.post(url, headers=headers, data=payload)

            try:
                data = response.json()
                print("Respuesta recibida:", data)

                dtes = None  # Evita error de variable no definida

                if isinstance(data, list):
                    dtes = data
                elif isinstance(data, dict) and "dtes" in data:
                    dtes = data["dtes"]
                else:
                    print("No se encontraron documentos o formato inesperado.")

                if not dtes:
                    print("No se encontraron documentos para ese RUT.")
                    continue  # Salta al siguiente cliente

                print(f"Se encontraron {len(dtes)} documentos para el RUT {rut}:\n")
                for dte in dtes:
                    customer = self.db.query(CustomerModel).filter(CustomerModel.rut == rut).first()

                    if not customer:
                        info_url = "https://libredte.cl/api/dte/contribuyentes/info/" + str(rut)
                        response = requests.get(info_url, headers=headers)
                        data = response.json()

                        print("Información del contribuyente:")
                        print(f"RUT: {data.get('rut')}-{data.get('dv')}")
                        print(f"Razón Social: {data.get('razon_social')}")
                        print(f"Giro: {data.get('giro')}")
                        print(f"Actividad Económica: {data.get('actividad_economica')}")
                        print(f"Teléfono: {data.get('telefono')}")
                        print(f"Email: {data.get('email')}")
                        print(f"Dirección: {data.get('direccion')}")
                        print(f"Comuna: {data.get('comuna')} ({data.get('comuna_glosa')})")

                        raw_phone = data.get("telefono", "")
                        cleaned_phone = raw_phone.replace("+56", "").replace(" ", "").strip()

                        commune_data = self.db.query(CommuneModel).filter(
                            func.lower(CommuneModel.commune).like(f"%{data.get('comuna_glosa', '').lower()}%")
                        ).first()

                        store_customer = CustomerModel(
                            rut=rut,
                            region_id=commune_data.region_id if commune_data else None,
                            commune_id=commune_data.id if commune_data else None,
                            customer=data.get('razon_social'),
                            address=data.get('direccion'),
                            activity=data.get('giro', ''),
                            phone=cleaned_phone,
                            email=data.get('email'),
                            added_date=datetime.now()
                        )

                        self.db.add(store_customer)
                        try:
                            self.db.commit()
                            print(f"Cliente {dte.get('razon_social', 'Cliente Desconocido')} guardado correctamente.")
                        except Exception as e:
                            print(f"Error al guardar el cliente: {str(e)}")

                    print(f"""
                            Tipo: {dte.get('tipo')}
                            Folio: {dte.get('folio')}
                            Razón Social: {dte.get('razon_social')}
                            Fecha: {dte.get('fecha')}
                            Total: {dte.get('total')}
                            Estado: {dte.get('estado')}
                            Track ID: {dte.get('track_id')}
                            Usuario: {dte.get('usuario')}
                            ¿Tiene XML?: {"Sí" if dte.get("has_xml") else "No"}
                            -----------------------------
                            """)

                    dte_qty = self.db.query(DteModel).filter(DteModel.folio == dte.get('folio')).count()
                    if dte_qty == 0:
                        if dte.get('tipo') == 'Factura electrónica':
                            dte_type_id = 33
                        elif dte.get('tipo') == 'Boleta electrónica':
                            dte_type_id = 39
                        elif dte.get('tipo') == 'Nota de crédito electrónica':
                            dte_type_id = 61
                        else:
                            continue  # Tipo desconocido

                        branch_office = self.db.query(BranchOfficeModel).filter(
                            BranchOfficeModel.dte_code == dte.get('sucursal_sii')
                        ).first()

                        validate_dte_existence = self.db.query(DteModel).filter(
                            DteModel.rut == rut,
                            DteModel.dte_type_id == dte_type_id,
                            DteModel.dte_version_id == 1,
                            DteModel.period == datetime.now().strftime('%Y-%m')
                        ).count()

                        branch_office_qty = self.db.query(BranchOfficeModel).filter(
                            BranchOfficeModel.dte_code == dte.get('sucursal_sii')
                        ).count()

                        if validate_dte_existence == 0 and branch_office_qty > 0:
                            store_dte = DteModel(
                                branch_office_id=branch_office.id,
                                cashier_id=0,
                                dte_type_id=dte_type_id,
                                dte_version_id=1,
                                status_id=4,
                                folio=dte.get('folio'),
                                rut=rut,
                                cash_amount=dte.get('total'),
                                card_amount=0,
                                subtotal=round(dte.get('total') / 1.19),
                                tax=dte.get('total') - round(dte.get('total') / 1.19),
                                discount=0,
                                total=dte.get('total'),
                                ticket_serial_number=0,
                                ticket_hour=0,
                                ticket_transaction_number=0,
                                ticket_dispenser_number=0,
                                ticket_number=0,
                                ticket_station_number=0,
                                ticket_sa=0,
                                ticket_correlative=0,
                                period = datetime.now().strftime('%Y-%m'),
                                entrance_hour='',
                                exit_hour='',
                                added_date=dte.get('fecha')
                            )

                            self.db.add(store_dte)
                        try:
                            self.db.commit()
                            print(f"DTE con folio {dte.get('folio')} guardado correctamente.")
                        except Exception as e:
                            print(f"Error al guardar el DTE con folio {dte.get('folio')}: {str(e)}")
                    else:
                        print(f"El DTE con folio {dte.get('folio')} ya existe en la base de datos.")
            except json.JSONDecodeError:
                print("La respuesta no es un JSON válido:")
                print(response.text)

    def get_total_quantity(user_inputs):

        if user_inputs['rol_id'] == 4 or user_inputs['rol_id'] == 5:
            user_inputs['rol_id'] = 1

        if user_inputs['rol_id'] == 3:
            user_inputs['rol_id'] = 4

        url = "https://jisparking.com/api/dte/receivable/"+ str(user_inputs['rol_id']) +"/"+ str(user_inputs['rut']) +"?api_token="+ str(user_inputs['api_token']) +""

        payload={}
        headers = {}

        response = requests.request("POST", url, headers=headers, data=payload)

        return response.text
    
    def get_total_amount(user_inputs):

        if user_inputs['rol_id'] == 4 or user_inputs['rol_id'] == 5:
            user_inputs['rol_id'] = 1

        if user_inputs['rol_id'] == 3:
            user_inputs['rol_id'] = 4
            
        url = "https://jisparking.com/api/dte/receivable/"+ str(user_inputs['rol_id']) +"/"+ str(user_inputs['rut']) +"?api_token="+ str(user_inputs['api_token']) +""

        payload={}
        headers = {}

        response = requests.request("POST", url, headers=headers, data=payload)

        return response.text
    
    def store(self, dte_inputs):
        dte_count = self.db.query(DteModel).filter(DteModel.folio == dte_inputs['folio']).count()

        if dte_count == 0:
            dte = DteModel(
                branch_office_id=dte_inputs['branch_office_id'],
                cashier_id=dte_inputs['cashier_id'],
                dte_type_id=dte_inputs['dte_type_id'],
                folio=dte_inputs['folio'],
                rut='66666666-6',
                cash_amount=dte_inputs['cash_amount'],
                card_amount=dte_inputs['card_amount'],
                subtotal=dte_inputs['subtotal'],
                tax=dte_inputs['tax'],
                discount=dte_inputs['discount'],
                total=dte_inputs['total'],
                ticket_serial_number=dte_inputs['ticket_serial_number'],
                ticket_hour=dte_inputs['ticket_hour'],
                ticket_transaction_number=dte_inputs['ticket_transaction_number'],
                ticket_dispenser_number=dte_inputs['ticket_dispenser_number'],
                ticket_number=dte_inputs['ticket_number'],
                ticket_station_number=dte_inputs['ticket_station_number'],
                ticket_sa=dte_inputs['ticket_sa'],
                ticket_correlative=dte_inputs['ticket_correlative'],
                entrance_hour=dte_inputs['entrance_hour'],
                exit_hour=dte_inputs['exit_hour'],
                added_date=dte_inputs['added_date']
            )

            self.db.add(dte)

            try:
                self.db.commit()
                return 1
            except Exception as e:
                error_message = str(e)
                return f"Error: {error_message}"
        else:
            return 2
        
    def existence(self, folio):
        # Filtra todos los registros que coincidan con los criterios especificados
        check_existence = self.db.query(DteModel)\
                            .filter(DteModel.folio == folio)\
                            .count()
        
        if check_existence > 0:
            return 1
        else:
            return 0

    def validate_quantity_tickets(self, total_machine_ticket, branch_office_id, cashier_id, added_date):
        # Convertir string a date
        added_date_obj = datetime.strptime(added_date, "%Y-%m-%d").date()

        start_date = datetime.combine(added_date_obj, datetime.min.time())
        end_date = start_date + timedelta(days=1)

        quantity = self.db.query(DteModel)\
            .filter(DteModel.branch_office_id == branch_office_id)\
            .filter(DteModel.cashier_id == cashier_id)\
            .filter(DteModel.added_date >= start_date)\
            .filter(DteModel.added_date < end_date)\
            .count()

        return 1 if quantity == total_machine_ticket else 0

        
    def verifiy_credit_note_amount(self, branch_office_id, cashier_id, added_date):
        amount = self.db.query(func.sum(DteModel.cash_amount))\
            .filter(DteModel.branch_office_id == branch_office_id)\
            .filter(DteModel.cashier_id == cashier_id)\
            .filter(DteModel.status_id == 5)\
            .filter(cast(DteModel.added_date, Date) == added_date)\
            .scalar()

        return amount or 0  # Retorna 0 si amount es None

    def delete(self, folio, branch_office_id, cashier_id, added_date, single):
        if single == 1:
            try:
                # Filtra todos los registros que coincidan con los criterios especificados
                data = self.db.query(DteModel)\
                            .filter(DteModel.branch_office_id == branch_office_id)\
                            .filter(DteModel.cashier_id == cashier_id)\
                            .filter(cast(DteModel.added_date, Date) == added_date)\
                            .filter(DteModel.folio == folio)\
                            .first()

                if data:
                    self.db.delete(data)
                    self.db.commit()
                    return 1
                else:
                    return "No data found"
            except Exception as e:
                error_message = str(e)
                return f"Error: {error_message}"
        else:
            try:
                # Filtra todos los registros que coincidan con los criterios especificados
                data = self.db.query(DteModel)\
                            .filter(DteModel.branch_office_id == branch_office_id)\
                            .filter(DteModel.cashier_id == cashier_id)\
                            .filter(cast(DteModel.added_date, Date) == added_date)\
                            .all()

                if data:
                    # Elimina todos los registros encontrados
                    for record in data:
                        self.db.delete(record)
                    self.db.commit()
                    return 1
                else:
                    return "No data found"
            except Exception as e:
                error_message = str(e)
                return f"Error: {error_message}"
            
    def open_customer_billing_period(self, period):
        current_period = HelperClass.fix_current_dte_period(period)

        last_period = HelperClass.fix_last_dte_period(period)

        dte_data = self.db.query(DteModel)\
                                .filter(DteModel.period == last_period)\
                                .filter(DteModel.status_id == 5)\
                                .filter(DteModel.dte_version_id == 1)\
                                .filter(DteModel.dte_type_id.in_([33, 39]))\
                                .all()
        
        if dte_data:
            for dte_datum in dte_data:

                added_date = HelperClass.create_period_date(period)

                dte = DteModel(
                        rut=dte_datum.rut,
                        branch_office_id=dte_datum.branch_office_id,
                        cashier_id=0,
                        dte_type_id=dte_datum.dte_type_id,
                        dte_version_id=1,
                        expense_type_id=25,
                        chip_id=0,
                        status_id=1,
                        cash_amount=dte_datum.cash_amount,
                        card_amount=0,
                        subtotal=dte_datum.subtotal,
                        tax=dte_datum.tax,
                        discount=0,
                        total=dte_datum.total,
                        period=current_period,
                        added_date=added_date
                    )
                
                # Agregar el objeto a la sesión
                self.db.add(dte)

                self.db.commit()
            try:
                return 'Opened period successfully'
            except Exception as e:
                error_message = str(e)
                return f"Error: {error_message}"
                
        else:
            return "No data found"

    def resend(self, dte_id, email):
        dte = self.db.query(DteModel).filter(DteModel.id == dte_id).first()

        url = "https://libredte.cl/api/dte/dte_emitidos/enviar_email/"+ str(dte.dte_type_id) +"/"+ str(dte.folio) +"/76063822"

        token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        payload = json.dumps({
            "emails": email,
            "asunto": None,
            "mensaje": None,
            "pdf": False,
            "cedible": False,
            "papelContinuo": 0
        })

        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        print(response.text)

    
    def get_massive_codes(self):
        period = datetime.now().strftime('%Y-%m')

        dte_data = (
            self.db.query(DteModel)
            .filter(DteModel.status_id == 5)
            .filter(DteModel.payment_type_id == 2)
            .filter(DteModel.dte_version_id == 1)
            .filter(DteModel.period == period)
            .filter(DteModel.comment.is_(None))
            .all()
        )

        token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
        search_url = "https://libredte.cl/api/pagos/cobros/buscar/76063822"
        base_info_url = "https://libredte.cl/api/pagos/cobros/info"
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        for dte in dte_data:
            print("Folio:", dte.folio)

            payload = {
                "codigo": None,
                "vencidos": None,
                "vencen_hoy": None,
                "vigentes": None,
                "sin_vencimiento": None,
                "dte_emitidos": None,
                "receptor": None,
                "dte": None,
                "folio": dte.folio,
                "fecha_desde": None,
                "fecha_hasta": None,
                "pagado": None,
                "pagado_desde": None,
                "pagado_hasta": None,
                "total": None,
                "total_desde": None,
                "total_hasta": None,
                "medio": None,
                "sucursal": None
            }

            try:
                # 1. Obtener código
                response = requests.post(search_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

                if data:
                    codigo = data[0].get("codigo")
                    print("Código extraído:", codigo)

                    # 2. Obtener info detallada
                    rut_emisor = "76063822-6"
                    info_url = f"{base_info_url}/{codigo}/{rut_emisor}?getDocumento=0&getDetalle=0&getLinks=0"

                    info_headers = {
                        'Accept': 'application/json',
                        'Authorization': f'Bearer {token}'
                    }

                    info_response = requests.get(info_url, headers=info_headers)
                    info_response.raise_for_status()
                    info_data = info_response.json()

                    # 3. Extraer authorizationCode
                    authorization_code = (
                        info_data
                        .get("datos", {})
                        .get("detailOutput", {})
                        .get("authorizationCode")
                    )

                    print("Authorization Code:", authorization_code)

                    # 4. Guardar en la BD
                    dte_record = (
                        self.db.query(DteModel)
                        .filter(DteModel.folio == dte.folio)
                        .filter(DteModel.dte_version_id == 1)
                        .first()
                    )

                    dte_record.comment = f"Código de autorización: {authorization_code}"
                    self.db.commit()
                    self.db.refresh(dte_record)

                else:
                    print("No hay resultados para este folio")

            except Exception as e:
                print(f"Error al procesar folio {dte.folio}: {str(e)}")

        return "Listo"

    def get_dte_authorization_code(self, folio: int):
        token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
        search_url = "https://libredte.cl/api/pagos/cobros/buscar/76063822"
        base_info_url = "https://libredte.cl/api/pagos/cobros/info"
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        dte = (
            self.db.query(DteModel)
            .filter(DteModel.folio == folio)
            .filter(DteModel.dte_version_id == 1)
            .first()
        )

        if not dte:
            print(f"No se encontró el DTE con folio {folio}")
            return 2

        print("Folio:", dte.folio)

        payload = {
            "codigo": None,
            "vencidos": None,
            "vencen_hoy": None,
            "vigentes": None,
            "sin_vencimiento": None,
            "dte_emitidos": None,
            "receptor": None,
            "dte": None,
            "folio": dte.folio,
            "fecha_desde": None,
            "fecha_hasta": None,
            "pagado": None,
            "pagado_desde": None,
            "pagado_hasta": None,
            "total": None,
            "total_desde": None,
            "total_hasta": None,
            "medio": None,
            "sucursal": None
        }

        try:
            # 1. Obtener código
            response = requests.post(search_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            if data:
                codigo = data[0].get("codigo")
                print("Código extraído:", codigo)

                # 2. Obtener info detallada
                rut_emisor = "76063822-6"
                info_url = f"{base_info_url}/{codigo}/{rut_emisor}?getDocumento=0&getDetalle=0&getLinks=0"

                info_response = requests.get(info_url, headers=headers)
                info_response.raise_for_status()
                info_data = info_response.json()

                # 3. Extraer authorizationCode
                authorization_code = (
                    info_data
                    .get("datos", {})
                    .get("detailOutput", {})
                    .get("authorizationCode")
                )

                print("Authorization Code:", authorization_code)

                if authorization_code:
                    # 4. Guardar en la BD
                    dte.comment = f"Código de autorización: {authorization_code}"
                    self.db.commit()
                    self.db.refresh(dte)
                    return 1

            print("No se obtuvo código o authorizationCode")
            return 2

        except Exception as e:
            print(f"Error al procesar folio {dte.folio}: {str(e)}")
            return 2

    def total_dtes_to_be_sent(self, branch_office_id, dte_type_id):
        """
        Obtiene la cantidad total de DTEs que deben ser enviados contando directamente desde DteModel
        con filtros específicos: status_id=2 (o status_id=14 para dte_type_id=61), dte_version_id=1, período actual, branch_office_id y dte_type_id
        
        Parámetros:
        - branch_office_id: ID de la sucursal (si es 0, cuenta todas las sucursales)
        - dte_type_id: ID del tipo de DTE (si es 0, cuenta todos los tipos)
        """
        try:
            current_period = datetime.now().strftime('%Y-%m')
            
            # Construir filtro base
            base_filter = [
                DteModel.period == current_period,
                DteModel.dte_version_id == 1
            ]
            
            # Aplicar filtro de status según el tipo de DTE
            if dte_type_id == 61:
                # Para notas de crédito, buscar status 2 o 14
                base_filter.append(DteModel.status_id.in_([2, 14]))
            else:
                # Para otros tipos de DTE, buscar status 2
                base_filter.append(DteModel.status_id == 2)
            
            # Si branch_office_id no es 0, filtrar por sucursal específica
            if branch_office_id != 0:
                base_filter.append(DteModel.branch_office_id == branch_office_id)
            
            # Si dte_type_id es mayor que 0, filtrar por tipo de DTE
            if dte_type_id > 0:
                base_filter.append(DteModel.dte_type_id == dte_type_id)
            
            quantity = self.db.query(DteModel).filter(*base_filter).count()
            
            return quantity
        except Exception as e:
            print(f"Error al obtener total DTEs to be sent: {str(e)}")
            return 0

    def decrease_dtes_to_be_sent(self):
        """
        Decrementa en 1 la cantidad total de DTEs que deben ser enviados en la tabla total_dtes_to_be_sent con id = 1
        """
        try:            
            total_record = self.db.query(TotalDtesToBeSentModel).filter(TotalDtesToBeSentModel.id == 1).first()
            if total_record and total_record.quantity > 0:
                total_record.quantity -= 1
                self.db.commit()
                print(f"✅ DTEs restantes por enviar: {total_record.quantity}")
                return total_record.quantity
            else:
                print("⚠️ No hay DTEs pendientes para decrementar")
                return 0
        except Exception as e:
            self.db.rollback()
            print(f"⚠️ Error al decrementar contador (tabla no actualizable): {str(e)}")
            print("ℹ️ El DTE se procesó correctamente, solo falló el contador")
            return 0

    def send_massive_dtes(self):
        """
        Envía WhatsApp masivamente para DTEs del período actual con status_id = 2
        """
        try:
            # Obtener el período actual en formato YYYY-MM
            current_period = datetime.now().strftime('%Y-%m')
            
            # Buscar DTEs del período actual con status_id = 2
            dtes = self.db.query(DteModel).filter(
                DteModel.period == current_period,
                DteModel.status_id == 2,
                DteModel.branch_office_id == 32
            ).all()
            
            whatsapp_class = WhatsappClass(self.db)
            successful_sends = 0
            failed_sends = 0
            results = []
            
            print(f"Enviando WhatsApp masivo para {len(dtes)} DTEs del período {current_period}")
            
            for dte in dtes:
                whatsapp_response = None
                customer_name = "No disponible"
                customer_phone = "No disponible"
                
                try:
                    # Obtener datos del cliente para todos los casos (siempre necesario para el response)
                    
                    customer = CustomerClass(self.db).get_by_rut(dte.rut)
                    customer_data = json.loads(customer)
                    
                    # Extraer nombre y teléfono del cliente
                    if customer_data and 'customer_data' in customer_data:
                        customer_name = customer_data['customer_data'].get('customer', 'No disponible')
                        customer_phone = customer_data['customer_data'].get('phone', 'No disponible')
                    
                    # Aplicar el mismo proceso que en generate_ticket/generate_bill según el tipo
                    # Si el DTE no tiene folio, necesita generarlo primero
                    if not dte.folio or dte.folio == 0:
                        
                        # Crear un objeto form_data simulado
                        form_data_sim = FormDataSimulator(dte)
                        
                        # Verificar el tipo de DTE para usar la clase correcta
                        if dte.dte_type_id == 39:  # Boleta electrónica
                            # Validar que no exista un DTE duplicado (misma validación que en customer_ticket_class)
                            check_dte_existence = self.db.query(DteModel).filter(
                                DteModel.branch_office_id == dte.branch_office_id,
                                DteModel.rut == dte.rut,
                                DteModel.total == (dte.cash_amount + 5000 if dte.chip_id == 1 else dte.cash_amount),
                                DteModel.dte_type_id == 39,
                                DteModel.dte_version_id == 1,
                                DteModel.status_id == 4,
                                DteModel.period == datetime.now().strftime('%Y-%m')
                            ).count()
                            
                            if check_dte_existence > 0:
                                raise Exception("Ya existe un DTE duplicado para este cliente en el período actual")
                            
                            # Crear instancia de CustomerTicketClass
                            customer_ticket_class = CustomerTicketClass(self.db)
                            
                            # Pre-generar el ticket
                            code = customer_ticket_class.pre_generate_ticket(customer_data, form_data_sim)
                            
                            if code is not None and code != 402:
                                # Generar el ticket con folio
                                folio = customer_ticket_class.generate_ticket(dte.rut, code)
                                
                                if folio:
                                    # Guardar PDF
                                    customer_ticket_class.save_pdf_ticket(folio)
                                    
                                    # Actualizar DTE con folio y status
                                    dte.folio = folio
                                    dte.status_id = 4
                                    self.db.commit()
                                    self.db.refresh(dte)
                                    
                                    # Enviar WhatsApp y capturar respuesta
                                    whatsapp_response = whatsapp_class.send(dte, dte.rut)
                                else:
                                    raise Exception("No se pudo generar el folio del ticket")
                            else:
                                raise Exception("Error en pre-generación del ticket")
                                
                        elif dte.dte_type_id == 33:  # Factura electrónica
                            # Validar que no exista un DTE duplicado (misma validación que en customer_bill_class)
                            check_dte_existence = self.db.query(DteModel).filter(
                                DteModel.branch_office_id == dte.branch_office_id,
                                DteModel.rut == dte.rut,
                                DteModel.total == (dte.cash_amount + 5000 if dte.chip_id == 1 else dte.cash_amount),
                                DteModel.dte_type_id == 33,
                                DteModel.dte_version_id == 1,
                                DteModel.status_id == 4,
                                DteModel.period == datetime.now().strftime('%Y-%m')
                            ).count()
                            
                            if check_dte_existence > 0:
                                raise Exception("Ya existe un DTE duplicado para este cliente en el período actual")
                            
                            # Crear instancia de CustomerBillClass
                            customer_bill_class = CustomerBillClass(self.db)
                            
                            # Pre-generar la factura
                            code = customer_bill_class.pre_generate_bill(customer_data, form_data_sim)
                            
                            if code is not None and code != 402:
                                # Generar la factura con folio
                                folio = customer_bill_class.generate_bill(dte.rut, code)
                                
                                if folio:
                                    # Guardar PDF
                                    customer_bill_class.save_pdf_bill(folio)
                                    
                                    # Actualizar DTE con folio y status
                                    dte.folio = folio
                                    dte.status_id = 4
                                    self.db.commit()
                                    self.db.refresh(dte)
                                    
                                    # Enviar WhatsApp y capturar respuesta
                                    whatsapp_response = whatsapp_class.send(dte, dte.rut)
                                else:
                                    raise Exception("No se pudo generar el folio de la factura")
                            else:
                                raise Exception("Error en pre-generación de la factura")
                        else:
                            raise Exception(f"Tipo de DTE no soportado: {dte.dte_type_id}")
                            
                    else:
                        # Si ya tiene folio, solo actualizar status y enviar WhatsApp
                        dte.status_id = 4
                        self.db.commit()
                        # Enviar WhatsApp y capturar respuesta
                        whatsapp_response = whatsapp_class.send(dte, dte.rut)
                    
                    # Verificar si WhatsApp fue exitoso
                    if whatsapp_response and whatsapp_response.get("whatsapp_accepted") == "accepted":
                        successful_sends += 1
                        
                        # Decrementar contador de DTEs pendientes
                        remaining_dtes = self.decrease_dtes_to_be_sent()
                        
                        results.append({
                            "id": dte.id,
                            "folio": dte.folio,
                            "rut": dte.rut,
                            "customer_name": customer_name,
                            "customer_phone": customer_phone,
                            "dte_type_id": dte.dte_type_id,
                            "status": "success",
                            "message": "DTE processed and WhatsApp sent successfully",
                            "whatsapp_response": whatsapp_response,
                            "remaining_dtes": remaining_dtes
                        })
                        
                        print(f"✅ DTE procesado y WhatsApp enviado para ID: {dte.id}, Folio: {dte.folio}, Tipo: {dte.dte_type_id}")
                    else:
                        # WhatsApp falló pero DTE se procesó
                        failed_sends += 1
                        
                        # Decrementar contador de DTEs pendientes (DTE se procesó aunque WhatsApp falló)
                        remaining_dtes = self.decrease_dtes_to_be_sent()
                        
                        results.append({
                            "id": dte.id,
                            "folio": dte.folio,
                            "rut": dte.rut,
                            "customer_name": customer_name,
                            "customer_phone": customer_phone,
                            "dte_type_id": dte.dte_type_id,
                            "status": "partial_success",
                            "message": "DTE processed but WhatsApp failed",
                            "whatsapp_response": whatsapp_response,
                            "remaining_dtes": remaining_dtes
                        })
                        
                        print(f"⚠️ DTE procesado pero WhatsApp falló para ID: {dte.id}, Folio: {dte.folio}, Tipo: {dte.dte_type_id}")
                    
                except Exception as e:
                    # Capturar cualquier error y continuar con el siguiente DTE
                    failed_sends += 1
                    
                    # Verificar si es un error de duplicado - NO ENVIAR WhatsApp
                    if "duplicado" in str(e).lower():
                        results.append({
                            "id": dte.id,
                            "folio": dte.folio if hasattr(dte, 'folio') else None,
                            "rut": dte.rut,
                            "customer_name": customer_name,
                            "customer_phone": customer_phone,
                            "dte_type_id": dte.dte_type_id,
                            "status": "duplicate_error",
                            "message": f"DTE duplicado detectado - No se envió WhatsApp: {str(e)}",
                            "whatsapp_response": None
                        })
                        
                        print(f"🚫 DTE duplicado detectado para ID: {dte.id}, RUT: {dte.rut}, Tipo: {dte.dte_type_id}: {str(e)}")
                    else:
                        # Otros errores
                        results.append({
                            "id": dte.id,
                            "folio": dte.folio if hasattr(dte, 'folio') else None,
                            "rut": dte.rut,
                            "customer_name": customer_name,
                            "customer_phone": customer_phone,
                            "dte_type_id": dte.dte_type_id,
                            "status": "error",
                            "message": f"Error processing DTE: {str(e)}",
                            "whatsapp_response": whatsapp_response
                        })
                        
                        print(f"❌ Error procesando DTE ID: {dte.id}, RUT: {dte.rut}, Tipo: {dte.dte_type_id}: {str(e)}")
                    
                    # Continuar con el siguiente DTE sin detener el foreach
                    continue
            
            return {
                "status": "success",
                "period": current_period,
                "total_dtes": len(dtes),
                "successful_sends": successful_sends,
                "failed_sends": failed_sends,
                "message": f"Envío masivo completado para período {current_period}. {successful_sends} exitosos, {failed_sends} fallidos.",
                "results": results
            }
            
        except Exception as e:
            print(f"Error en envío masivo de WhatsApp: {str(e)}")
            return {
                "status": "error",
                "message": f"Error en envío masivo: {str(e)}"
            }

    def _generate_complete_dte(self, dte):
        """
        Método auxiliar para generar un DTE completo (folio, PDF, etc.)
        Retorna dict con status y pdf_url
        """
        try:
            # Obtener datos del cliente
            customer = CustomerClass(self.db).get_by_rut(dte.rut)
            customer_data = json.loads(customer)
            
            # Si el DTE ya tiene folio, solo necesitamos el URL del PDF
            if dte.folio and dte.folio != 0:
                pdf_url = f"https://jisparking.com/api/backend/dtes/download_pdf/{dte.folio}/{dte.dte_type_id}"
                return {
                    "status": "success",
                    "message": "DTE ya generado",
                    "pdf_url": pdf_url
                }
            
            # Crear un objeto form_data simulado
            form_data_sim = FormDataSimulator(dte)
            
            # Generar según el tipo de DTE
            if dte.dte_type_id == 39:  # Boleta electrónica
                # Validar duplicados
                check_dte_existence = self.db.query(DteModel).filter(
                    DteModel.branch_office_id == dte.branch_office_id,
                    DteModel.rut == dte.rut,
                    DteModel.total == (dte.cash_amount + 5000 if dte.chip_id == 1 else dte.cash_amount),
                    DteModel.dte_type_id == 39,
                    DteModel.dte_version_id == 1,
                    DteModel.status_id == 4,
                    DteModel.period == datetime.now().strftime('%Y-%m')
                ).count()
                
                if check_dte_existence > 0:
                    raise Exception("Ya existe un DTE duplicado para este cliente en el período actual")
                
                # Generar ticket
                customer_ticket_class = CustomerTicketClass(self.db)
                code = customer_ticket_class.pre_generate_ticket(customer_data, form_data_sim)
                
                if code is not None and code != 402:
                    folio = customer_ticket_class.generate_ticket(dte.rut, code)
                    if folio:
                        customer_ticket_class.save_pdf_ticket(folio)
                        # Actualizar DTE
                        dte.folio = folio
                        dte.status_id = 4
                        self.db.commit()
                        self.db.refresh(dte)
                        
                        pdf_url = f"https://jisparking.com/api/backend/dtes/download_pdf/{folio}/{dte.dte_type_id}"
                        return {
                            "status": "success",
                            "message": "Ticket generado exitosamente",
                            "pdf_url": pdf_url
                        }
                    else:
                        return {"status": "error", "message": "No se pudo generar el folio del ticket"}
                else:
                    return {"status": "error", "message": "Error en pre-generación del ticket"}
                    
            elif dte.dte_type_id == 33:  # Factura electrónica
                # Validar duplicados
                check_dte_existence = self.db.query(DteModel).filter(
                    DteModel.branch_office_id == dte.branch_office_id,
                    DteModel.rut == dte.rut,
                    DteModel.total == (dte.cash_amount + 5000 if dte.chip_id == 1 else dte.cash_amount),
                    DteModel.dte_type_id == 33,
                    DteModel.dte_version_id == 1,
                    DteModel.status_id == 4,
                    DteModel.period == datetime.now().strftime('%Y-%m')
                ).count()
                
                if check_dte_existence > 0:
                    raise Exception("Ya existe un DTE duplicado para este cliente en el período actual")
                
                # Generar factura
                customer_bill_class = CustomerBillClass(self.db)
                code = customer_bill_class.pre_generate_bill(customer_data, form_data_sim)
                
                if code is not None and code != 402:
                    folio = customer_bill_class.generate_bill(dte.rut, code)
                    if folio:
                        customer_bill_class.save_pdf_bill(folio)
                        # Actualizar DTE
                        dte.folio = folio
                        dte.status_id = 4
                        self.db.commit()
                        self.db.refresh(dte)
                        
                        pdf_url = f"https://jisparking.com/api/backend/dtes/download_pdf/{folio}/{dte.dte_type_id}"
                        return {
                            "status": "success",
                            "message": "Factura generada exitosamente",
                            "pdf_url": pdf_url
                        }
                    else:
                        return {"status": "error", "message": "No se pudo generar el folio de la factura"}
                else:
                    return {"status": "error", "message": "Error en pre-generación de la factura"}
            elif dte.dte_type_id == 61:  # Nota de crédito electrónica
                try:
                    # Para notas de crédito, usar la clase CustomerTicketBillClass
                    customer_ticket_bill_class = CustomerTicketBillClass(self.db)
                    
                    # Crear form_data para nota de crédito
                    credit_note_form = CreditNoteFormDataSimulator(dte.id)
                    
                    # Generar la nota de crédito (rol_id = 1 para envío masivo, is_massive_sending=True)
                    folio = customer_ticket_bill_class.store_credit_note(credit_note_form, rol_id=1, is_massive_sending=True)
                except Exception as credit_note_error:
                    return {"status": "error", "message": f"Error en generación de nota de crédito para DTE {dte.id} (RUT: {dte.rut}): {str(credit_note_error)}"}
                
                if folio and folio != "Error generating credit note":
                    # Actualizar DTE - para notas de crédito cambiar status de 14 a 5
                    dte.folio = folio
                    dte.status_id = 5  # Status final para notas de crédito
                    self.db.commit()
                    self.db.refresh(dte)
                    
                    pdf_url = f"https://jisparking.com/api/backend/dtes/download_pdf/{folio}/{dte.dte_type_id}"
                    return {
                        "status": "success",
                        "message": "Nota de crédito generada exitosamente",
                        "pdf_url": pdf_url
                    }
                else:
                    return {"status": "error", "message": "No se pudo generar la nota de crédito"}
            else:
                return {"status": "error", "message": f"Tipo de DTE no soportado: {dte.dte_type_id}"}
                
        except Exception as e:
            return {"status": "error", "message": f"Error generando DTE: {str(e)}"}

    def send_massive_dtes_streaming(self, branch_office_id, dte_type_id):
        """
        Generador que envía WhatsApp masivamente y produce progreso en tiempo real
        Yields dict con información de progreso para cada DTE procesado
        
        Parámetros:
        - branch_office_id: ID de la sucursal (si es 0, procesa todas las sucursales)
        - dte_type_id: ID del tipo de DTE (si es 0, procesa todos los tipos)
        """
        try:
            # Obtener DTEs del período actual
            current_period = datetime.now().strftime('%Y-%m')
            
            # Construir filtro base
            # Para tipo 61 (notas de crédito) aceptar tanto status_id = 2 como 14
            if dte_type_id == 61:
                status_filter = DteModel.status_id.in_([2, 14])
            else:
                # Si no se especifica tipo o es diferente de 61, incluir ambos status
                if dte_type_id == 0:
                    status_filter = DteModel.status_id.in_([2, 14])
                else:
                    status_filter = DteModel.status_id == 2
            
            base_filter = [
                DteModel.period == current_period,
                status_filter,
                DteModel.dte_version_id == 1
            ]
            
            # Si branch_office_id es 0, procesar todas las sucursales
            if branch_office_id != 0:
                base_filter.append(DteModel.branch_office_id == branch_office_id)
            
            # Si dte_type_id es mayor que 0, filtrar por tipo de DTE
            if dte_type_id > 0:
                base_filter.append(DteModel.dte_type_id == dte_type_id)
            
            # Información de depuración para diagnóstico
            expected_status = 14 if dte_type_id == 61 else (2 if dte_type_id != 0 else "2 o 14")
            branch_info = f"sucursal {branch_office_id}" if branch_office_id != 0 else "todas las sucursales"
            type_info = f"tipo {dte_type_id}" if dte_type_id != 0 else "todos los tipos"
            
            # Enviar mensaje inicial con información de filtros
            yield {
                "type": "init",
                "period": current_period,
                "branch_office_id": branch_office_id,
                "dte_type_id": dte_type_id,
                "expected_status": expected_status,
                "message": f"Iniciando envío masivo para {type_info} en {branch_info} del período {current_period}"
            }
            
            dtes = self.db.query(DteModel).filter(*base_filter).all()
            
            # Información adicional de depuración si no hay DTEs
            if not dtes:
                # Contar DTEs en la sucursal sin filtro de status para diagnóstico
                debug_filter = [
                    DteModel.period == current_period,
                    DteModel.dte_version_id == 1
                ]
                if branch_office_id != 0:
                    debug_filter.append(DteModel.branch_office_id == branch_office_id)
                if dte_type_id > 0:
                    debug_filter.append(DteModel.dte_type_id == dte_type_id)
                
                total_in_period = self.db.query(DteModel).filter(*debug_filter).count()
                
                # Obtener información de status de DTEs existentes para diagnóstico
                
                status_counts = {}
                if total_in_period > 0:
                    # Contar DTEs por status_id
                    status_query = self.db.query(DteModel.status_id, func.count(DteModel.id)).filter(*debug_filter).group_by(DteModel.status_id).all()
                    for status_id, count in status_query:
                        status_counts[status_id] = count
                
                debug_message = f"No hay DTEs para procesar en {branch_info} de {type_info}. "
                debug_message += f"Total en período: {total_in_period}. "
                if status_counts:
                    status_info = ", ".join([f"status {s}: {c} DTEs" for s, c in status_counts.items()])
                    debug_message += f"Status encontrados: [{status_info}]"
        
                yield {
                    "type": "complete",
                    "total_dtes": 0,
                    "processed": 0,
                    "successful_sends": 0,
                    "failed_sends": 0,
                    "branch_office_id": branch_office_id,
                    "dte_type_id": dte_type_id,
                    "message": debug_message
                }
                return
            
            total_dtes = len(dtes)
            successful_sends = 0
            failed_sends = 0
            processed = 0
            
            # Procesar cada DTE individualmente
            for i, dte in enumerate(dtes, 1):
                try:
                    processed += 1
                    
                    # Enviar progreso
                    yield {
                        "type": "progress",
                        "current": i,
                        "total": total_dtes,
                        "percentage": round((i / total_dtes) * 100, 2),
                        "processing_dte": {
                            "id": dte.id,
                            "rut": dte.rut,
                            "dte_type_id": dte.dte_type_id
                        },
                        "successful_sends": successful_sends,
                        "failed_sends": failed_sends,
                        "message": f"Procesando DTE {i}/{total_dtes}"
                    }
                    
                    # Validar duplicado
                    duplicate_filter = [
                        DteModel.rut == dte.rut,
                        DteModel.dte_type_id == dte.dte_type_id,
                        DteModel.period == current_period,
                        DteModel.id != dte.id
                    ]
                    
                    # Si branch_office_id no es 0, filtrar por sucursal específica
                    if branch_office_id != 0:
                        duplicate_filter.append(DteModel.branch_office_id == branch_office_id)
                    
                    existing_dte = self.db.query(DteModel).filter(*duplicate_filter).first()
                    
                    if existing_dte:
                        failed_sends += 1
                        yield {
                            "type": "dte_result",
                            "dte_id": dte.id,
                            "status": "duplicate_skipped",
                            "message": f"DTE duplicado - Saltado (existe ID: {existing_dte.id})",
                            "current": i,
                            "total": total_dtes
                        }
                        continue
                    
                    # Generar el DTE completo
                    generation_result = self._generate_complete_dte(dte)
                    
                    if generation_result.get("status") == "error":
                        failed_sends += 1
                        yield {
                            "type": "dte_result",
                            "dte_id": dte.id,
                            "status": "generation_error",
                            "message": generation_result.get("message", "Error en generación"),
                            "current": i,
                            "total": total_dtes
                        }
                        continue
                    
                    # Refrescar el objeto DTE desde la BD para obtener cambios
                    self.db.refresh(dte)
                    
                    # Verificar y asegurar que el status se actualizó correctamente
                    # Para notas de crédito (tipo 61), el status debe ser 5
                    # Para otros tipos (33, 39), el status debe ser 4
                    if dte.dte_type_id == 61:
                        if dte.status_id != 5:
                            dte.status_id = 5
                            self.db.commit()
                            self.db.refresh(dte)
                    else:
                        if dte.status_id != 4:
                            dte.status_id = 4
                            self.db.commit()
                            self.db.refresh(dte)
                    
                    # Obtener datos del cliente
                    customer_name = "Cliente no encontrado"
                    customer_phone = None
                    
                    customer_class = CustomerClass(self.db)
                    customer_response = customer_class.get_by_rut(dte.rut)
                    
                    if customer_response and customer_response != "No se encontraron datos para el campo especificado." and not customer_response.startswith("Error:"):
                        try:
                            customer_data = json.loads(customer_response)
                            if customer_data and 'customer_data' in customer_data:
                                customer_name = customer_data['customer_data'].get('customer', 'Cliente no encontrado')
                                customer_phone = customer_data['customer_data'].get('phone', 'No disponible')
                        except (json.JSONDecodeError, TypeError, AttributeError) as e:
                            # Si hay error parseando el JSON o accediendo a los datos, usar valores por defecto
                            customer_name = "Cliente no encontrado"
                            customer_phone = "No disponible"
                    
                    # Enviar WhatsApp
                    whatsapp_class = WhatsappClass(self.db)
                    whatsapp_response = whatsapp_class.send(dte, dte.rut)
                    
                    # Obtener contador actualizado desde DteModel
                    try:
                        # Usar la misma lógica de filtro que al inicio
                        if dte_type_id == 61:
                            remaining_status_filter = DteModel.status_id.in_([2, 14])
                        else:
                            if dte_type_id == 0:
                                remaining_status_filter = DteModel.status_id.in_([2, 14])
                            else:
                                remaining_status_filter = DteModel.status_id == 2
                        
                        remaining_filter = [
                            DteModel.period == current_period,
                            remaining_status_filter,
                            DteModel.dte_version_id == 1
                        ]
                        
                        # Si branch_office_id no es 0, filtrar por sucursal específica
                        if branch_office_id != 0:
                            remaining_filter.append(DteModel.branch_office_id == branch_office_id)
                        
                        remaining_dtes = self.db.query(DteModel).filter(*remaining_filter).count()
                    except:
                        remaining_dtes = 0
                    
                    if whatsapp_response and whatsapp_response.get("status") == "success":
                        successful_sends += 1
                        
                        yield {
                            "type": "dte_result",
                            "dte_id": dte.id,
                            "status": "success",
                            "message": "WhatsApp enviado exitosamente",
                            "customer_name": customer_name,
                            "customer_phone": customer_phone,
                            "current": i,
                            "total": total_dtes,
                            "remaining_dtes": remaining_dtes,
                            "whatsapp_status": whatsapp_response.get("status"),
                            "whatsapp_response": whatsapp_response
                        }
                    else:
                        failed_sends += 1
                        yield {
                            "type": "dte_result",
                            "dte_id": dte.id,
                            "status": "whatsapp_error",
                            "message": f"Error enviando WhatsApp: {whatsapp_response.get('message') if whatsapp_response else 'Sin respuesta'}",
                            "current": i,
                            "total": total_dtes,
                            "remaining_dtes": remaining_dtes,
                            "whatsapp_status": whatsapp_response.get("status") if whatsapp_response else "no_response",
                            "whatsapp_response": whatsapp_response
                        }
                        
                except Exception as e:
                    # Rollback en caso de error
                    self.db.rollback()
                    failed_sends += 1
                    processed += 1
                    
                    # Obtener contador actualizado incluso en errores
                    try:
                        # Usar la misma lógica de filtro que al inicio
                        if dte_type_id == 61:
                            error_status_filter = DteModel.status_id == 14
                        else:
                            if dte_type_id == 0:
                                error_status_filter = DteModel.status_id.in_([2, 14])
                            else:
                                error_status_filter = DteModel.status_id == 2
                        
                        error_remaining_filter = [
                            DteModel.period == current_period,
                            error_status_filter,
                            DteModel.dte_version_id == 1
                        ]
                        
                        # Si branch_office_id no es 0, filtrar por sucursal específica
                        if branch_office_id != 0:
                            error_remaining_filter.append(DteModel.branch_office_id == branch_office_id)
                        
                        remaining_dtes = self.db.query(DteModel).filter(*error_remaining_filter).count()
                    except:
                        remaining_dtes = 0
                    
                    # Detectar si es error de duplicado
                    if "Duplicate entry" in str(e):
                        yield {
                            "type": "dte_result",
                            "dte_id": dte.id,
                            "status": "duplicate_error",
                            "message": f"DTE duplicado detectado: {str(e)}",
                            "current": i,
                            "total": total_dtes,
                            "remaining_dtes": remaining_dtes,
                            "whatsapp_status": "not_sent",
                            "whatsapp_response": None
                        }
                    else:
                        yield {
                            "type": "dte_result",
                            "dte_id": dte.id,
                            "status": "error",
                            "message": f"Error procesando DTE: {str(e)}",
                            "current": i,
                            "total": total_dtes,
                            "remaining_dtes": remaining_dtes,
                            "whatsapp_status": "not_sent",
                            "whatsapp_response": None
                        }
            
            # Obtener contador actualizado desde DteModel
            try:
                # Usar la misma lógica de filtro que al inicio
                if dte_type_id == 61:
                    final_status_filter = DteModel.status_id == 14
                else:
                    if dte_type_id == 0:
                        final_status_filter = DteModel.status_id.in_([2, 14])
                    else:
                        final_status_filter = DteModel.status_id == 2
                
                final_remaining_filter = [
                    DteModel.period == current_period,
                    final_status_filter,
                    DteModel.dte_version_id == 1
                ]
                
                # Si branch_office_id no es 0, filtrar por sucursal específica
                if branch_office_id != 0:
                    final_remaining_filter.append(DteModel.branch_office_id == branch_office_id)
                
                # Si dte_type_id es mayor que 0, filtrar por tipo de DTE
                if dte_type_id > 0:
                    final_remaining_filter.append(DteModel.dte_type_id == dte_type_id)
                
                remaining_dtes = self.db.query(DteModel).filter(*final_remaining_filter).count()
                branch_info = f" (sucursal {branch_office_id})" if branch_office_id != 0 else " (todas las sucursales)"
                print(f"✅ DTEs restantes por enviar{branch_info}: {remaining_dtes}")
            except Exception as e:
                remaining_dtes = 0
                print(f"⚠️ Error al obtener contador actualizado: {str(e)}")
            
            # Resultado final
            if branch_office_id != 0:
                # Obtener el nombre de la sucursal
                branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == branch_office_id).first()
                branch_name = branch_office.branch_office if branch_office else f"Sucursal {branch_office_id}"
                branch_scope = f" ({branch_name})"
            else:
                branch_scope = " (todas las sucursales)"
      
            yield {
                "type": "complete",
                "period": current_period,
                "total_dtes": total_dtes,
                "processed": processed,
                "successful_sends": successful_sends,
                "failed_sends": failed_sends,
                "remaining_dtes": remaining_dtes,
                "branch_office_id": branch_office_id,
                "message": f"Envío masivo completado{branch_scope}. {successful_sends} exitosos, {failed_sends} fallidos. Restantes: {remaining_dtes}"
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "message": f"Error en envío masivo: {str(e)}"
            }

    def debug_dte_type_61_status(self, branch_office_id=None):
        """
        Función de debug para verificar el status de DTEs tipo 61
        """
        try:
            current_period = datetime.now().strftime('%Y-%m')
            
            # Filtro base
            filters = [
                DteModel.dte_type_id == 61,
                DteModel.dte_version_id == 1,
                DteModel.period == current_period
            ]
            
            if branch_office_id:
                filters.append(DteModel.branch_office_id == branch_office_id)
            
            # Contar por status
            status_counts = self.db.query(
                DteModel.status_id, 
                func.count(DteModel.id)
            ).filter(*filters).group_by(DteModel.status_id).all()
            
            # Obtener detalles de algunos DTEs
            sample_dtes = self.db.query(
                DteModel.id,
                DteModel.folio, 
                DteModel.status_id,
                DteModel.rut,
                DteModel.branch_office_id,
                DteModel.period
            ).filter(*filters).limit(10).all()
            
            result = {
                "period": current_period,
                "branch_office_id": branch_office_id,
                "total_type_61": sum([count for _, count in status_counts]),
                "status_breakdown": {status: count for status, count in status_counts},
                "sample_dtes": [
                    {
                        "id": dte.id,
                        "folio": dte.folio,
                        "status_id": dte.status_id,
                        "rut": dte.rut,
                        "branch_office_id": dte.branch_office_id,
                        "period": dte.period
                    } for dte in sample_dtes
                ]
            }
            
            return result
            
        except Exception as e:
            return {"error": str(e)}

    def get_dte_data(self, dte_type_id: int, folio: int, issuer: str = "76063822"):
        try:
            url = f"https://libredte.cl/api/dte/dte_emitidos/info/{dte_type_id}/{folio}/{issuer}"
            token = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
            
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {token}'
            }
            
            print(f"Consultando LibreDTE: {url}")
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "status_code": response.status_code,
                    "data": data
                }
            else:
                return {
                    "status": "error",
                    "status_code": response.status_code,
                    "message": f"Error al consultar LibreDTE: {response.text}",
                    "data": None
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "status_code": None,
                "message": f"Error de conexión con LibreDTE: {str(e)}",
                "data": None
            }
        except Exception as e:
            return {
                "status": "error", 
                "status_code": None,
                "message": f"Error inesperado: {str(e)}",
                "data": None
            }
