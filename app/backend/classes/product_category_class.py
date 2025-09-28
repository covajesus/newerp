from app.backend.db.models import ProductCategoryModel
from sqlalchemy.orm import Session

class ProductCategoryClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(ProductCategoryModel). \
                    order_by(ProductCategoryModel.product_category). \
                    all()
            
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
