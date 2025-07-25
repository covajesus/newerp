import requests
from app.backend.db.models import DteModel, BranchOfficeModel, CustomerModel, SupplierModel, CommuneModel
from sqlalchemy import desc
from sqlalchemy.dialects import mysql
from app.backend.classes.helper_class import HelperClass
from sqlalchemy import cast, Date, func
from datetime import datetime, timedelta
from sqlalchemy import or_
from dateutil.relativedelta import relativedelta
import json

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
            from sqlalchemy.dialects import mysql
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
            from sqlalchemy.dialects import mysql
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

            # Obtener la consulta SQL generada con literal_binds=True
            query_sql = str(query.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))

            # Reemplazar %% por % para corregir el problema de escape
            query_sql = query_sql.replace('%%', '%')

            # Mostrar la consulta SQL corregida
            print("Consulta SQL corregida:", query_sql)

            # Calcular el offset para la paginación
            offset = (page - 1) * items_per_page

            # Ejecutar la consulta con paginación
            data = self.db.execute(query.statement.offset(offset).limit(items_per_page)).fetchall()

            # Procesar los resultados
            total_items = len(data)  # Total de elementos
            total_pages = (total_items + items_per_page - 1) // items_per_page  # Calcular total de páginas
            data_paginated = data  # Paginar los resultados según el offset y el límite

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
            } for dte in data_paginated]

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

    from datetime import datetime, timedelta

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
                valid_branch_ids = [8, 10, 13, 15, 16, 18, 20, 33, 34, 39, 41, 45, 48, 50, 52, 57, 60, 61, 71, 76, 78, 81, 90, 102, 106, 112]

                if dte_datum.branch_office_id in valid_branch_ids:
                    added_date = HelperClass.create_period_date(period)

                    dte = DteModel(
                        rut=dte_datum.rut,
                        branch_office_id=dte_datum.branch_office_id,
                        cashier_id=0,
                        dte_type_id=dte_datum.dte_type_id,
                        dte_version_id=1,
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
