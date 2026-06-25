from datetime import datetime

from app.backend.db.models import DteLineItemNameModel


class DteLineItemNameClass:
    def __init__(self, db):
        self.db = db

    def get(self, row_id: int):
        try:
            return (
                self.db.query(DteLineItemNameModel)
                .filter(DteLineItemNameModel.id == row_id)
                .first()
            )
        except Exception as e:
            return f"Error: {str(e)}"

    def get_list(self):
        try:
            return (
                self.db.query(DteLineItemNameModel)
                .order_by(DteLineItemNameModel.item_name)
                .all()
            )
        except Exception as e:
            return f"Error: {str(e)}"

    def get_all(self, page=1, items_per_page=10):
        try:
            query = self.db.query(
                DteLineItemNameModel.id,
                DteLineItemNameModel.item_name,
            ).order_by(DteLineItemNameModel.item_name)

            if page > 0:
                total_items = query.count()
                total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
                if total_items == 0:
                    return {
                        "total_items": 0,
                        "total_pages": 1,
                        "current_page": 1,
                        "items_per_page": items_per_page,
                        "data": [],
                    }
                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()
                serialized_data = [
                    {"id": row.id, "item_name": row.item_name} for row in data
                ]
                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data,
                }

            data = query.all()
            return [{"id": row.id, "item_name": row.item_name} for row in data]
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def store(self, form_data):
        name = (form_data.item_name or "").strip()
        if not name:
            return "Error: item_name is required"

        exists = (
            self.db.query(DteLineItemNameModel)
            .filter(DteLineItemNameModel.item_name == name)
            .count()
        )
        if exists:
            return "Error: item_name already exists"

        now = datetime.now()
        row = DteLineItemNameModel(
            item_name=name,
            added_date=now,
            updated_date=now,
        )
        self.db.add(row)
        try:
            self.db.commit()
            return "Dte line item name stored successfully"
        except Exception as e:
            self.db.rollback()
            return f"Error: {str(e)}"

    def delete(self, row_id: int):
        try:
            deleted = (
                self.db.query(DteLineItemNameModel)
                .filter(DteLineItemNameModel.id == row_id)
                .delete()
            )
            self.db.commit()
            if not deleted:
                return {"status": "error", "message": "Record not found"}
            return {"status": "success", "message": "Dte line item name deleted successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}

    def update(self, form_data):
        name = (form_data.item_name or "").strip()
        if not name:
            return "Error: item_name is required"

        row = (
            self.db.query(DteLineItemNameModel)
            .filter(DteLineItemNameModel.id == form_data.id)
            .first()
        )
        if not row:
            return "Dte line item name not found"

        duplicate = (
            self.db.query(DteLineItemNameModel)
            .filter(
                DteLineItemNameModel.item_name == name,
                DteLineItemNameModel.id != form_data.id,
            )
            .count()
        )
        if duplicate:
            return "Error: item_name already exists"

        row.item_name = name
        row.updated_date = datetime.now()
        try:
            self.db.commit()
            return "Dte line item name updated successfully"
        except Exception as e:
            self.db.rollback()
            return f"Error: {str(e)}"
