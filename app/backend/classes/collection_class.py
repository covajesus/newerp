from app.backend.db.models import CollectionModel
from datetime import datetime

class CollectionClass:
    def get(self, search_inputs = None, page = 1, items_per_page = 10):
            
        data_query = self.db.query(CollectionModel).order_by('added_date')

        total_items = data_query.count()
        total_pages = (total_items + items_per_page - 1)

        data = data_query.all()

        if not data:
            return "No data found"
 
        serialized_data = [{
            "id": collection.id,
            "branch_office_id": collection.branch_office_id,
        } for collection in data]

        return {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page,
            "items_per_page": items_per_page,
            "data": serialized_data
        }


    def store(self, collection_inputs):
        current_date = datetime.now().strftime('%Y-%m-%d')

        collection_count = self.db.query(CollectionModel).filter(CollectionModel.cashier_id == collection_inputs['cashier_id']).filter(CollectionModel.branch_office_id == collection_inputs['branch_office_id']).filter(CollectionModel.added_date == current_date).count()

        if collection_count == 0:
            collection = CollectionModel(
                branch_office_id=collection_inputs['branch_office_id'],
                cashier_id=collection_inputs['cashier_id'],
                cash_gross_amount=collection_inputs['cash_gross_amount'],
                cash_net_amount=collection_inputs['cash_net_amount'],
                card_gross_amount=collection_inputs['card_gross_amount'],
                card_net_amount=collection_inputs['card_net_amount'],
                total_tickets=collection_inputs['total_tickets'],
                added_date=current_date
            )

            self.db.add(collection)

            try:
                self.db.commit()
                return 1
            except Exception as e:
                error_message = str(e)
                return f"Error: {error_message}"
        else:
            collection = self.db.query(CollectionModel).filter(CollectionModel.cashier_id == collection_inputs['cashier_id']).filter(CollectionModel.branch_office_id == collection_inputs['branch_office_id']).filter(CollectionModel.added_date == current_date).first()
            collection.cash_gross_amount = collection_inputs['cash_gross_amount']
            collection.cash_net_amount = collection_inputs['cash_net_amount']
            collection.card_gross_amount = collection_inputs['card_gross_amount']
            collection.card_net_amount = collection_inputs['card_net_amount']
            collection.total_tickets = collection_inputs['total_tickets']
            collection.updated_date = current_date
            self.db.add(collection)
            self.db.commit()
            
            return 1