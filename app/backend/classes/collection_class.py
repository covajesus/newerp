from app.backend.db.models import CollectionModel

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