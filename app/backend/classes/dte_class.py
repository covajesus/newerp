import requests
from app.backend.db.models import DteModel, BranchOfficeModel, CustomerModel, SupplierModel
from sqlalchemy import desc
from sqlalchemy.dialects import mysql
from app.backend.classes.helper_class import HelperClass
from sqlalchemy import cast, Date, func
from datetime import datetime, timedelta

class DteClass:
    def __init__(self, db):
        self.db = db

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

    def get_all_with_customer(self, folio=None, branch_office_id=None, rut=None, customer=None, since=None, until=None, amount=None, supervisor_id=None, status_id=None, dte_version_id=None, page=0, items_per_page=10):
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
                filters.append(CustomerModel.customer.like(f"%{customer}%"))
            if until is not None:
                filters.append(DteModel.added_date <= until)  # Fecha desde
            if since is not None:
                filters.append(DteModel.added_date >= since)  # Fecha hasta
            if amount is not None:
                filters.append(DteModel.total == amount)
            if supervisor_id is not None:
                filters.append(DteModel.supervisor_id == supervisor_id)
            if status_id is not None:
                filters.append(DteModel.status_id == status_id)

            filters.append(DteModel.rut != None)
            filters.append(DteModel.dte_version_id == dte_version_id)
            filters.append(DteModel.status_id > 3)

            # Construir la consulta base con los filtros aplicados
            query = self.db.query(
                DteModel.id, 
                DteModel.branch_office_id, 
                DteModel.folio, 
                DteModel.total, 
                DteModel.entrance_hour,
                DteModel.exit_hour,
                DteModel.status_id,
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
                desc(DteModel.folio)
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
                "dte_type_id": dte.dte_type_id,
                "total": dte.total,
                "customer": dte.customer,
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
            filters.append(DteModel.dte_type_id == dte_type_id)

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
                desc(DteModel.folio)
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

        print(current_period)
        last_period = HelperClass.fix_last_dte_period(period)
        print(last_period)

        dte_data = self.db.query(DteModel)\
                            .filter(DteModel.period == last_period)\
                            .filter(DteModel.status_id == 5)\
                            .all()

        print(dte_data)
        
        if dte_data:
            for dte_datum in dte_data:
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