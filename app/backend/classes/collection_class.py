from app.backend.db.models import CollectionModel, BranchOfficeModel, DepositModel, TotalAllCollectionModel, TotalAllCollectionPerSupervisorModel, CashierModel, TotalGeneralCollectionModel, TotalCollectionModel, TotalDetailCollectionModel, CashierModel
from datetime import datetime
from app.backend.classes.dte_class import DteClass
from sqlalchemy import desc
from sqlalchemy.dialects import mysql
from sqlalchemy import func
import pytz
from app.backend.classes.authentication_class import AuthenticationClass
import json
from datetime import date, timedelta
from sqlalchemy import and_
from sqlalchemy import func, cast, Date

class CollectionClass:
    def __init__(self, db):
        self.db = db

    def update_all_collections(self, collections_data: list):
        for data in collections_data:
            tz = pytz.timezone('America/Santiago')
            current_date = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

            # si data es tupla, conviértelo a dict con índices o nombres
            # suponiendo que sabes el orden de campos, por ejemplo:
            # (cashier_id, branch_office_id, added_date, cash_gross_amount, card_gross_amount, card_net_amount, total_tickets)

            # Ejemplo de asignación por posición (ajusta el orden según tu query)
            cashier_id = data[3]
            branch_office_id = data[2]
            added_date = data[4]
            cash_gross_amount = data[6]
            cash_net_amount = data[7]  # Asumiendo que este es el campo correcto
            card_gross_amount = data[8]
            card_net_amount = data[9]
            total_tickets = data[10]

            # Buscar registro existente
            record = self.db.query(CollectionModel).filter_by(
                cashier_id=cashier_id,
                branch_office_id=branch_office_id,
                added_date=added_date
            ).first()

            if record:
                if record.cash_gross_amount != cash_gross_amount or record.card_gross_amount != card_gross_amount:
                    record.cash_gross_amount = cash_gross_amount
                    record.cash_net_amount = cash_net_amount
                    record.card_gross_amount = card_gross_amount
                    record.card_net_amount = card_net_amount
                    record.total_tickets = total_tickets
                    record.updated_date = current_date

                    self.db.commit()
            else:
                new_data = {
                    'cashier_id': cashier_id,
                    'branch_office_id': branch_office_id,
                    'added_date': added_date,
                    'cash_gross_amount': cash_gross_amount,
                    'cash_net_amount': cash_net_amount,
                    'card_gross_amount': card_gross_amount,
                    'card_net_amount': card_net_amount,
                    'total_tickets': total_tickets,
                    'updated_date': current_date
                }
                new_record = CollectionModel(**new_data)
                self.db.add(new_record)

                self.db.commit()


    def get_all_collections(self, branch_office_id=None, since=None, until=None):
        """
        Obtiene todas las colecciones con filtros opcionales.
        
        Parámetros:
        - branch_office_id: ID de la sucursal (opcional)
        - since: Fecha desde en formato 'YYYY-MM-DD' (opcional, por defecto últimos 10 días)
        - until: Fecha hasta en formato 'YYYY-MM-DD' (opcional, por defecto hoy)
        """
        # Si no se proporciona since, usar los últimos 10 días por defecto
        if since is None:
            limit_date = date.today() - timedelta(days=10)
        else:
            try:
                limit_date = datetime.strptime(since, '%Y-%m-%d').date()
            except ValueError:
                limit_date = date.today() - timedelta(days=10)
        
        # Si no se proporciona until, usar hoy
        if until is None:
            until_date = date.today()
        else:
            try:
                until_date = datetime.strptime(until, '%Y-%m-%d').date()
            except ValueError:
                until_date = date.today()

        query = (
            self.db.query(
                CashierModel.cashier,
                CollectionModel.id,
                CollectionModel.branch_office_id,
                CollectionModel.cashier_id,
                CollectionModel.added_date,
                CollectionModel.total_tickets,
                CollectionModel.cash_gross_amount,
                CollectionModel.cash_net_amount,
                CollectionModel.card_gross_amount,
                CollectionModel.card_net_amount,
                CollectionModel.total_tickets
            )
            .outerjoin(CollectionModel, CollectionModel.cashier_id == CashierModel.id)
            .filter(CollectionModel.added_date >= limit_date)
            .filter(CollectionModel.added_date <= until_date)
        )
        
        # Aplicar filtro de branch_office_id si se proporciona
        if branch_office_id is not None:
            query = query.filter(CollectionModel.branch_office_id == branch_office_id)
        
        data = query.all()

        return data
    
    def get(self, id):
        try:
            data_query = self.db.query(CashierModel.cashier, CollectionModel.id, CollectionModel.branch_office_id, CollectionModel.cashier_id, CollectionModel.added_date, CollectionModel.total_tickets, CollectionModel.cash_gross_amount, CollectionModel.cash_gross_amount, CollectionModel.cash_net_amount, CollectionModel.card_gross_amount, CollectionModel.card_net_amount).outerjoin(CollectionModel, CollectionModel.cashier_id == CashierModel.id).filter(CollectionModel.id == id).first()

            if data_query:
                # Serializar los datos del empleado
                collection_data = {
                    "id": data_query.id,
                    "branch_office_id": data_query.branch_office_id,
                    "cashier": data_query.cashier,
                    "cashier_id": data_query.cashier_id,
                    "added_date": data_query.added_date.strftime('%Y-%m-%d'),
                    "total_tickets": data_query.total_tickets,
                    "cash_gross_amount": data_query.cash_gross_amount,
                    "cash_net_amount": data_query.cash_net_amount,
                    "card_gross_amount": data_query.card_gross_amount,
                    "card_net_amount": data_query.card_net_amount
                }

                result = {
                    "collection_data": collection_data
                }

                # Convierte el resultado a una cadena JSON
                serialized_result = json.dumps(result)

                return serialized_result
            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get_all(self, rol_id = None, rut = None, branch_office_id = None, cashier_id = None, added_date = None, page = 1, items_per_page = 10):
        if rol_id == 1 or rol_id == 2:
            filters = []
            if branch_office_id is not None:
                filters.append(TotalGeneralCollectionModel.branch_office_id == branch_office_id)
            if cashier_id is not None:
                filters.append(TotalGeneralCollectionModel.cashier_id == cashier_id)
            if added_date is not None and added_date != "":
                print(added_date)
                filters.append(TotalGeneralCollectionModel.added_date == added_date)

            try:
                # Construir la consulta base con los filtros aplicados
                query = self.db.query(
                    TotalGeneralCollectionModel.id, 
                    TotalGeneralCollectionModel.branch_office_id, 
                    TotalGeneralCollectionModel.cashier_id, 
                    BranchOfficeModel.branch_office,
                    CashierModel.cashier,
                    TotalGeneralCollectionModel.total, 
                    TotalGeneralCollectionModel.card_total_collections,
                    TotalGeneralCollectionModel.total_tickets, 
                    TotalGeneralCollectionModel.added_date,
                    TotalGeneralCollectionModel.updated_date,
                ).outerjoin(BranchOfficeModel, BranchOfficeModel.id == TotalGeneralCollectionModel.branch_office_id).outerjoin(CashierModel, CashierModel.id == TotalGeneralCollectionModel.cashier_id).filter(*filters).order_by(desc(TotalGeneralCollectionModel.added_date))
                print(query)
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
                        "id": collection.id,
                        "branch_office_id": collection.branch_office_id,
                        "branch_office": collection.branch_office,
                        "cashier_id": collection.cashier_id,
                        "cashier": collection.cashier,
                        "cash_gross_amount": collection.total,
                        "card_gross_amount": collection.card_total_collections,
                        "total_tickets": collection.total_tickets,
                        "added_date": collection.added_date.strftime('%d-%m-%Y') if collection.added_date else None,
                        "updated_date": collection.updated_date
                    } for collection in data]

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
                        "id": collection.id,
                        "branch_office_id": collection.branch_office_id,
                        "branch_office": collection.branch_office,
                        "cashier_id": collection.cashier_id,
                        "cashier": collection.cashier,
                        "cash_gross_amount": collection.total,
                        "card_gross_amount": collection.card_total_collections,
                        "total_tickets": collection.total_tickets,
                        "added_date": collection.added_date.strftime('%d-%m-%Y') if collection.added_date else None,
                        "updated_date": collection.updated_date
                    } for collection in data]

                    return serialized_data

            except Exception as e:
                error_message = str(e)
                return {"status": "error", "message": error_message}
            
        elif rol_id == 4:
            filters = []
            if branch_office_id is not None:
                filters.append(TotalGeneralCollectionModel.branch_office_id == branch_office_id)
            if cashier_id is not None:
                filters.append(TotalGeneralCollectionModel.cashier_id == cashier_id)
            if added_date is not None and added_date != "":
                print(added_date)
                filters.append(TotalGeneralCollectionModel.added_date == added_date)

            try:
                # Construir la consulta base con los filtros aplicados
                query = self.db.query(
                    TotalGeneralCollectionModel.id, 
                    TotalGeneralCollectionModel.branch_office_id, 
                    TotalGeneralCollectionModel.cashier_id, 
                    BranchOfficeModel.branch_office,
                    CashierModel.cashier,
                    TotalGeneralCollectionModel.total, 
                    TotalGeneralCollectionModel.card_total_collections,
                    TotalGeneralCollectionModel.total_tickets, 
                    TotalGeneralCollectionModel.added_date,
                    TotalGeneralCollectionModel.updated_date,
                ).outerjoin(BranchOfficeModel, BranchOfficeModel.id == TotalGeneralCollectionModel.branch_office_id).outerjoin(CashierModel, CashierModel.id == TotalGeneralCollectionModel.cashier_id).filter(BranchOfficeModel.principal_supervisor == rut).filter(*filters).order_by(desc(TotalGeneralCollectionModel.added_date))

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
                        "id": collection.id,
                        "branch_office_id": collection.branch_office_id,
                        "branch_office": collection.branch_office,
                        "cashier_id": collection.cashier_id,
                        "cashier": collection.cashier,
                        "cash_gross_amount": collection.total,
                        "card_gross_amount": collection.card_total_collections,
                        "total_tickets": collection.total_tickets,
                        "added_date": collection.added_date,
                        "updated_date": collection.updated_date
                    } for collection in data]

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
                        "id": collection.id,
                        "branch_office_id": collection.branch_office_id,
                        "branch_office": collection.branch_office,
                        "cashier_id": collection.cashier_id,
                        "cashier": collection.cashier,
                        "cash_gross_amount": collection.cash_gross_amount,
                        "card_gross_amount": collection.card_gross_amount,
                        "total_tickets": collection.total_tickets,
                        "added_date": collection.added_date,
                        "updated_date": collection.updated_date
                    } for collection in data]

                    return serialized_data

            except Exception as e:
                error_message = str(e)
                return {"status": "error", "message": error_message}
        
    def get_all_with_detail(self, branch_office_id = None, cashier_id = None, added_date = None, page = 1, items_per_page = 10):
        filters = []
        if branch_office_id is not None:
            filters.append(TotalCollectionModel.branch_office_id == branch_office_id)
        if cashier_id is not None:
            filters.append(TotalCollectionModel.cashier_id == cashier_id)
        if added_date is not None and added_date != "":
            filters.append(TotalCollectionModel.added_date == added_date)

        try:
            # Construir la consulta base con los filtros aplicados
            query = self.db.query(
                        TotalCollectionModel.id, 
                        TotalCollectionModel.branch_office_id, 
                        TotalCollectionModel.cashier_id, 
                        BranchOfficeModel.branch_office,
                        CashierModel.cashier,
                        TotalCollectionModel.cash_total, 
                        TotalCollectionModel.card_total,
                        TotalCollectionModel.total_tickets, 
                        TotalCollectionModel.added_date,
                        TotalDetailCollectionModel.cash_total,
                        TotalDetailCollectionModel.card_total,
                        TotalDetailCollectionModel.total_tickets
                    ).outerjoin(
                        BranchOfficeModel, BranchOfficeModel.id == TotalCollectionModel.branch_office_id
                    ).outerjoin(
                        CashierModel, CashierModel.id == TotalCollectionModel.cashier_id
                    ).outerjoin(
                        TotalDetailCollectionModel, 
                        (TotalDetailCollectionModel.cashier_id == TotalCollectionModel.cashier_id) &
                        (TotalDetailCollectionModel.added_date == TotalCollectionModel.added_date)
                    ).filter(*filters).order_by(
                        desc(TotalCollectionModel.added_date)
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
                    "id": collection.id,
                    "branch_office_id": collection.branch_office_id,
                    "branch_office": collection.branch_office,
                    "cashier_id": collection.cashier_id,
                    "cashier": collection.cashier,
                    "cash_gross_amount": collection.cash_total,
                    "card_gross_amount": collection.card_total,
                    "total_tickets": collection.total_tickets,
                    "dtes_cash_total": collection.cash_total,
                    "dtes_card_total": collection.card_total,
                    "dtes_total_tickets": collection.total_tickets,
                    "added_date": collection.added_date
                } for collection in data]

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
                    "id": collection.id,
                    "branch_office_id": collection.branch_office_id,
                    "branch_office": collection.branch_office,
                    "cashier_id": collection.cashier_id,
                    "cashier": collection.cashier,
                    "cash_gross_amount": collection.cash_total,
                    "card_gross_amount": collection.card_total,
                    "total_tickets": collection.total_tickets,
                    "dtes_cash_total": collection.cash_total,
                    "dtes_card_total": collection.card_total,
                    "dtes_total_tickets": collection.total_tickets,
                    "added_date": collection.added_date
                } for collection in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
        
    def total_collection(self, branch_office_id, collection_date):
        try:
            result = self.db.query(
                func.sum(TotalGeneralCollectionModel.total).label('total'), 
                func.max(TotalGeneralCollectionModel.id).label('collection_id')
            ).filter(
                TotalGeneralCollectionModel.branch_office_id == branch_office_id,
                TotalGeneralCollectionModel.added_date == collection_date
            ).group_by(
                TotalGeneralCollectionModel.branch_office_id
            ).first()

 
            if result:
                return {
                    'total': result.total if result and result.total else 0,
                    'collection_id': result.collection_id
                }
            else:
                return {'total': 0, 'collection_id': None}
        except Exception as e:
            error_message = str(e)
            return {'error': error_message}
        
    def existence(self, branch_office_id, cashier_id, added_date):
        try:
            existence = self.db.query(CollectionModel).filter(
                CollectionModel.branch_office_id == branch_office_id,
                CollectionModel.cashier_id == cashier_id,
                CollectionModel.added_date == added_date
            ).first()
            
            return existence  # Retorna el objeto o None
        except Exception as e:
            print(f"Error checking collection existence: {e}")
            raise e  # Lanza la excepción para manejo en store
    
    def store_redcomercio(self, cashier_id, branch_office_id, gross_total, net_total, total_tickets, date):
        print(cashier_id, branch_office_id, gross_total, net_total, total_tickets, date)
        collection = CollectionModel(
                branch_office_id=branch_office_id,
                cashier_id=cashier_id,
                cash_gross_amount=gross_total,
                cash_net_amount=net_total,
                card_gross_amount=0,
                card_net_amount=0,
                subscribers=0,
                total_tickets=total_tickets,
                added_date=date,
                updated_date=str(date) + " 00:00:00"
            )

        self.db.add(collection)

        self.db.commit()

    def update(self, update_collection_inputs):
        tz = pytz.timezone('America/Santiago')
        current_date = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

        try:
            collection = self.db.query(CollectionModel).filter(
                CollectionModel.id == update_collection_inputs.id
            ).first()

            if collection:
                collection.cash_gross_amount = update_collection_inputs.cash_gross_amount
                collection.cash_net_amount = update_collection_inputs.cash_net_amount
                collection.card_gross_amount = update_collection_inputs.card_gross_amount
                collection.card_net_amount = update_collection_inputs.card_net_amount
                collection.total_tickets = update_collection_inputs.total_tickets
                collection.updated_date = current_date

                self.db.commit()
                return "Collection updated successfully"
            else:
                return "Collection not found"

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def total_collections(self, rol_id = None):
        if rol_id == 1 or rol_id == 2:
            total = self.db.query(
                TotalAllCollectionModel.total
            ).first()
        elif rol_id == 4:
            total = self.db.query(
                TotalAllCollectionPerSupervisorModel.total
            ).first()

        return total[0] if total else 0
    
    def update_deposits(self):

        results = (
                self.db.query(
                    func.sum(CollectionModel.cash_gross_amount).label("total_cash"),
                    cast(CollectionModel.added_date, Date).label("added_day"),
                    CollectionModel.branch_office_id
                )
                .filter(CollectionModel.added_date >= '2024-01-01')
                .group_by(
                    CollectionModel.branch_office_id,
                    cast(CollectionModel.added_date, Date)
                )
                .all()
            )
        
        for result in results:
            deposits = self.db.query(DepositModel).filter(DepositModel.branch_office_id == result.branch_office_id).filter(DepositModel.collection_date == result.added_day).all()

            for deposit in deposits:
                if deposit:
                    print(result.added_day)
                    print(result.total_cash)

                    total_cash = result.total_cash if result.total_cash else 0
        
                    deposit_detail = self.db.query(DepositModel).filter(DepositModel.id == deposit.id).first()

                    if deposit_detail:
                        deposit_detail.collection_amount = total_cash
                        deposit_detail.updated_date = func.now()
                        self.db.commit()
                else:
                    print(f"[✘] No hay datos para sucursal {deposit.branch_office_id} en fecha {deposit.collection_date}")
    
    def update_redcomercio (self, cashier_id, branch_office_id, gross_total, net_total, total_tickets, date):
        collection = self.db.query(CollectionModel).filter(
            CollectionModel.cashier_id == cashier_id,
            CollectionModel.branch_office_id == branch_office_id,
            CollectionModel.added_date == date
        ).first()

        if collection:
            collection.cash_gross_amount = gross_total
            collection.cash_net_amount = net_total
            collection.total_tickets = total_tickets
            collection.updated_date = str(date) + " 00:00:00"

            self.db.commit()
        else:
            return "No se encontró la colección para actualizar."

    def store(self, collection_inputs):
        try:
            tz = pytz.timezone('America/Santiago')
            current_date = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

            # Verificar si ya existe la colección
            existing_collection = self.existence(
                collection_inputs['branch_office_id'], 
                collection_inputs['cashier_id'], 
                collection_inputs['added_date']
            )

            credit_note_amount = DteClass(self.db).verifiy_credit_note_amount(
                collection_inputs['branch_office_id'], 
                collection_inputs['cashier_id'], 
                collection_inputs['added_date']
            )

            check_token_status = AuthenticationClass(self.db).check_simplefactura_token()

            if check_token_status == 0:
                print('El token está vencido.')
                AuthenticationClass(self.db).create_simplefactura_token()
            else:
                print('El token está vigente.')

            # Calcular montos con descuento de nota de crédito
            if credit_note_amount > 0:
                cash_gross_total = int(collection_inputs['cash_gross_amount']) - int(credit_note_amount)
                cash_net_total = round(int(cash_gross_total)/1.19)
            else:
                cash_gross_total = int(collection_inputs['cash_gross_amount'])
                cash_net_total = round(int(cash_gross_total)/1.19)

            if existing_collection is None:
                # Crear nueva colección
                collection = CollectionModel(
                    branch_office_id=collection_inputs['branch_office_id'],
                    cashier_id=collection_inputs['cashier_id'],
                    cash_gross_amount=cash_gross_total,
                    cash_net_amount=cash_net_total,
                    card_gross_amount=collection_inputs['card_gross_amount'],
                    card_net_amount=collection_inputs['card_net_amount'],
                    total_tickets=collection_inputs['total_tickets'],
                    added_date=collection_inputs['added_date'],
                    updated_date=current_date
                )

                self.db.add(collection)
                self.db.commit()
                return "Collection stored successfully"
            else:
                # Actualizar colección existente si hay cambios
                input_cash_gross = int(collection_inputs['cash_gross_amount'])
                input_card_gross = int(collection_inputs['card_gross_amount'])
                
                if (existing_collection.cash_gross_amount != input_cash_gross or 
                    existing_collection.card_gross_amount != input_card_gross):
                    
                    existing_collection.cash_gross_amount = cash_gross_total
                    existing_collection.cash_net_amount = cash_net_total
                    existing_collection.card_gross_amount = collection_inputs['card_gross_amount']
                    existing_collection.card_net_amount = collection_inputs['card_net_amount']
                    existing_collection.total_tickets = collection_inputs['total_tickets']
                    existing_collection.updated_date = current_date
                    
                    self.db.commit()
                    return "Collection updated successfully"
                else:
                    return "Collection already exists with same values"
                    
        except Exception as e:
            self.db.rollback()
            error_message = str(e)
            print(f"Error in store method: {error_message}")
            return f"Error: {error_message}"
        
    def manual_store(self, collection_inputs):
        tz = pytz.timezone('America/Santiago')
        current_date = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

        collection = CollectionModel(
                branch_office_id=collection_inputs['branch_office_id'],
                cashier_id=collection_inputs['cashier_id'],
                cash_gross_amount=collection_inputs['cash_gross_amount'],
                cash_net_amount=collection_inputs['cash_net_amount'],
                card_gross_amount=collection_inputs['card_gross_amount'],
                card_net_amount=collection_inputs['card_net_amount'],
                total_tickets=collection_inputs['total_tickets'],
                added_date=collection_inputs['added_date'],
                updated_date=current_date
            )

        self.db.add(collection)

        try:
            self.db.commit()
            return "Collection stored successfully"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            self.db.query(CollectionModel).filter(CollectionModel.id == id).delete()
            self.db.commit()

            return {"status": "success", "message": "Collection deleted successfully"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def delete_red_comercio_collection(self, branch_office_id, cashier_id, added_date):
        try:
            validate_existence = self.db.query(CollectionModel).filter(
                CollectionModel.branch_office_id == branch_office_id,
                CollectionModel.cashier_id == cashier_id,
                CollectionModel.added_date == added_date
            ).delete()

            self.db.commit()

            return 1

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}