from app.backend.db.models import DepositModel

class DepositClass:
    def __init__(self, db):
        self.db = db

    def get(self, search_inputs = None, page = 1, items_per_page = 10):
            
        data_query = self.db.query(DepositModel).order_by('added_date')

        if search_inputs != None:
            if search_inputs['branch_office_id'] != None and search_inputs['branch_office_id'] != 0 and search_inputs['branch_office_id'] != '':
                data_query = data_query.filter(DepositModel.branch_office_id == search_inputs['branch_office_id'])
            if search_inputs['status_id'] != None and search_inputs['status_id'] != 0 and search_inputs['status_id'] != '':
                data_query = data_query.filter(DepositModel.status_id == search_inputs['status_id'])
            if search_inputs['since'] != None and search_inputs['since'] != '':
                data_query = data_query.filter(DepositModel.added_date >= search_inputs['since'])
            if search_inputs['until'] != None and search_inputs['until'] != '':
                data_query = data_query.filter(DepositModel.added_date <= search_inputs['until'])

        total_items = data_query.count()
        total_pages = (total_items + items_per_page - 1)

        data = data_query.all()

        if not data:
            return "No data found"
 
        serialized_data = [{
            "id": deposit.id,
            "branch_office_id": deposit.branch_office_id,
            "deposit_type_id": deposit.deposit_type_id,
            "collection_id": deposit.collection_id,
            "status_id": deposit.status_id,
            "deposit_amount": deposit.deposit_amount,
            "deposit_number": deposit.deposit_number,
            "collection_amount": deposit.collection_amount,
            "card_collection_amount": deposit.card_collection_amount,
            "collection_date": deposit.collection_date,
            "support": deposit.support,
            "added_date": deposit.added_date,
            "updated_date": deposit.updated_date,
        } for deposit in data]

        return {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page,
            "items_per_page": items_per_page,
            "data": serialized_data
        }