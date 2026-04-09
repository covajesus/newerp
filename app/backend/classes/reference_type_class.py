from app.backend.db.models import ReferenceTypeModel


class ReferenceTypeClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        rows = (
            self.db.query(ReferenceTypeModel)
            .order_by(ReferenceTypeModel.sort_order, ReferenceTypeModel.code)
            .all()
        )
        return [
            {
                "id": r.id,
                "code": r.code,
                "description": r.description,
                "sort_order": r.sort_order,
            }
            for r in rows
        ]
