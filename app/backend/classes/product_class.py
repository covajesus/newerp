from app.backend.db.models import ProductModel
from sqlalchemy.orm import Session

class ProductClass:
    def __init__(self, db: Session):
        self.db = db

    def get_list(self):
        try:
            data = self.db.query(ProductModel). \
                    filter(ProductModel.visibility_id == 1). \
                    order_by(ProductModel.description). \
                    all()
            
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def get_all(self, page=1, items_per_page=10, code=None, description=None):
        try:
            # Consulta base de productos con todos los campos
            data_query = self.db.query(
                ProductModel.id,
                ProductModel.product_category_id,
                ProductModel.visibility_id,
                ProductModel.code,
                ProductModel.description,
                ProductModel.min_stock,
                ProductModel.max_stock,
                ProductModel.measure,
                ProductModel.balance,
                ProductModel.added_date,
                ProductModel.updated_date
            ).filter(
                ProductModel.visibility_id == 1
            )
            
            # Aplicar filtros opcionales
            if code is not None:
                data_query = data_query.filter(ProductModel.code == code)
            
            if description is not None:
                data_query = data_query.filter(ProductModel.description.ilike(f"%{description}%"))
            
            # Ordenar por descripción
            data_query = data_query.order_by(ProductModel.description.asc())
            
            # Aplicar paginación
            data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()
            total_items = data_query.count()
            total_pages = (total_items + items_per_page - 1) // items_per_page

            if page < 1 or page > total_pages:
                return "Invalid page number"

            if not data:
                return "No data found"

            # Serializar los datos
            serialized_data = [{
                "id": product.id,
                "product_category_id": product.product_category_id,
                "visibility_id": product.visibility_id,
                "code": product.code,
                "description": product.description,
                "min_stock": product.min_stock,
                "max_stock": product.max_stock,
                "measure": product.measure,
                "balance": product.balance,
                "added_date": product.added_date,
                "updated_date": product.updated_date
            } for product in data]

            return {
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "items_per_page": items_per_page,
                "data": serialized_data
            }

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"