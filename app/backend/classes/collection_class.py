from app.backend.db.models import CollectionModel, BranchOfficeModel, CashierModel, TotalGeneralCollectionModel, TotalCollectionModel, TotalDetailCollectionModel
from datetime import datetime
from app.backend.classes.setting_class import SettingClass
from sqlalchemy import desc
from sqlalchemy.dialects import mysql
from sqlalchemy import func
import pytz
from app.backend.classes.authentication_class import AuthenticationClass

class CollectionClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, branch_office_id = None, cashier_id = None, added_date = None, page = 1, items_per_page = 10):
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
                TotalGeneralCollectionModel.id.label('collection_id')
            ).filter(
                TotalGeneralCollectionModel.branch_office_id == branch_office_id
            ).filter(
                TotalGeneralCollectionModel.added_date == collection_date
            ).group_by(TotalGeneralCollectionModel.id).all()

            if result:
                total_sum = result[0][0]
                collection_id = result[0][1]
                return {
                    'total': total_sum if total_sum else 0,
                    'collection_id': collection_id
                }
            else:
                return {'total': 0, 'collection_id': None}
        except Exception as e:
            error_message = str(e)
            return {'error': error_message}

    def get(self, field, value):
        try:
            data = self.db.query(CollectionModel).filter(getattr(CollectionModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def existence(self, branch_office_id, cashier_id, added_date):
        try:
            existence = self.db.query(CollectionModel).filter(CollectionModel.branch_office_id == branch_office_id).filter(CollectionModel.cashier_id == cashier_id).filter(CollectionModel.added_date == added_date).count()
            
            if existence > 0:
                return 1
            else:
                return 0
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def store(self, collection_inputs):
        print(collection_inputs)
        tz = pytz.timezone('America/Santiago')
        current_date = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

        collection_count = self.existence(collection_inputs['branch_office_id'], collection_inputs['cashier_id'], collection_inputs['added_date'])

        check_token_status = AuthenticationClass(self.db).check_simplefactura_token()

        if check_token_status == 0:
            print('El token está vencido.')

            AuthenticationClass(self.db).create_simplefactura_token()
        else:
            print('El token está vigente.')

        if collection_count == 0:
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
        else:
            check_collection = self.db.query(CollectionModel).filter(
                CollectionModel.cashier_id == collection_inputs['cashier_id'],
                CollectionModel.branch_office_id == collection_inputs['branch_office_id'],
                CollectionModel.added_date == collection_inputs['added_date']
            ).first()
            
            print(check_collection.added_date)
            print(collection_inputs['added_date'])
            
            if check_collection.cash_gross_amount != collection_inputs['cash_gross_amount'] or check_collection.card_gross_amount != collection_inputs['card_gross_amount']:
                print(check_collection.id)

            
            return "Collection updated successfully"