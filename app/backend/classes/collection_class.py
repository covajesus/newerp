from app.backend.db.models import CollectionModel
from datetime import datetime
from sqlalchemy import desc

class CollectionClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, search_inputs = None, page = 1, items_per_page = 10):
            
        data_query = self.db.query(CollectionModel).order_by(desc(CollectionModel.added_date))

        total_items = data_query.count()
        total_pages = (total_items + items_per_page - 1)

        data = data_query.all()

        if not data:
            return "No data found"
 
        serialized_data = [{
            "id": collection.id,
            "branch_office_id": collection.branch_office_id,
            "cashier_id": collection.cashier_id,
            "cash_gross_amount": collection.cash_gross_amount,
            "cash_net_amount": collection.cash_net_amount,
            "card_gross_amount": collection.card_gross_amount,
            "card_net_amount": collection.card_net_amount,
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
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        collection_count = self.existence(collection_inputs['branch_office_id'], collection_inputs['cashier_id'], collection_inputs['added_date'])

        if collection_count == 0:
            collection = CollectionModel(
                branch_office_id=collection_inputs['branch_office_id'],
                cashier_id=collection_inputs['cashier_id'],
                cash_gross_amount=collection_inputs['cash_gross_amount'],
                cash_net_amount=collection_inputs['cash_net_amount'],
                card_gross_amount=collection_inputs['card_gross_amount'],
                card_net_amount=collection_inputs['card_net_amount'],
                total_tickets=collection_inputs['total_tickets'],
                added_date=collection_inputs['added_date']
            )

            self.db.add(collection)

            try:
                self.db.commit()
                return "Collection stored successfully"
            except Exception as e:
                error_message = str(e)
                return f"Error: {error_message}"
        else:
            check_collection = self.db.query(CollectionModel).filter(CollectionModel.cashier_id == collection_inputs['cashier_id']).filter(CollectionModel.branch_office_id == collection_inputs['branch_office_id']).filter(CollectionModel.added_date == collection_inputs['added_date']).first()
            
            if check_collection.cash_gross_amount != collection_inputs['cash_gross_amount'] or check_collection.card_gross_amount != collection_inputs['card_gross_amount']:
                collection = self.db.query(CollectionModel).filter(CollectionModel.cashier_id == collection_inputs['cashier_id']).filter(CollectionModel.branch_office_id == collection_inputs['branch_office_id']).filter(CollectionModel.added_date == collection_inputs['added_date']).first()
                collection.cash_gross_amount = collection_inputs['cash_gross_amount']
                collection.cash_net_amount = collection_inputs['cash_net_amount']
                collection.card_gross_amount = collection_inputs['card_gross_amount']
                collection.card_net_amount = collection_inputs['card_net_amount']
                collection.total_tickets = collection_inputs['total_tickets']
                collection.updated_date = current_date
                self.db.add(collection)
                self.db.commit()
            
            return "Collection updated successfully"