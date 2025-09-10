from app.backend.db.models import ProductModel
from sqlalchemy.orm import Session

class ProductClass:
    def __init__(self, db: Session):
        self.db = db

    def get_list(self):
        try:
            data = self.db.query(ProductModel). \
                    order_by(ProductModel.description). \
                    all()
            
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"