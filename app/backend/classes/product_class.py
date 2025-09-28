from app.backend.db.models import ProductModel, ProductCategoryModel, ExpenseTypeModel
from sqlalchemy.orm import Session
from sqlalchemy import func, text

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
            # Consulta base de productos con LEFT JOIN a product_categories y expense_types
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
                ProductModel.updated_date,
                ProductCategoryModel.product_category,
                ExpenseTypeModel.expense_type,
                ExpenseTypeModel.id.label('expense_type_id')
            ).outerjoin(
                ProductCategoryModel, ProductCategoryModel.id == ProductModel.product_category_id
            ).outerjoin(
                ExpenseTypeModel, 
                text("expense_types.accounting_account COLLATE utf8mb4_unicode_ci = product_categories.accounting_account COLLATE utf8mb4_unicode_ci")
            )
            
            # Aplicar filtros opcionales siguiendo el patrón de DTEs
            if code is not None and code != '':
                data_query = data_query.filter(ProductModel.code.like(f"%{code}%"))
            
            if description is not None and description != '':
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

            # Serializar los datos incluyendo información de categoría y expense_type
            serialized_data = [{
                "id": product.id,
                "product_category_id": product.product_category_id,
                "visibility_id": product.visibility_id,
                "code": product.code,
                "description": product.description,
                "expense_type_id": product.expense_type_id,
                "min_stock": product.min_stock,
                "max_stock": product.max_stock,
                "measure": product.measure,
                "balance": product.balance,
                "added_date": product.added_date,
                "updated_date": product.updated_date,
                "product_category": product.product_category,
                "expense_type": product.expense_type
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

    def get(self, field, value):
        try:
            data = self.db.query(ProductModel).filter(getattr(ProductModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def store(self, product_inputs):
        try:
            product = ProductModel()
            product.product_category_id = product_inputs.product_category_id
            product.visibility_id = product_inputs.visibility_id
            product.code = product_inputs.code
            product.description = product_inputs.description
            product.min_stock = product_inputs.min_stock
            product.max_stock = product_inputs.max_stock
            product.measure = product_inputs.measure
            product.balance = product_inputs.balance
            
            self.db.add(product)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def delete(self, id):
        try:
            data = self.db.query(ProductModel).filter(ProductModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def update(self, id, form_data):
        try:
            existing_product = self.db.query(ProductModel).filter(ProductModel.id == id).one_or_none()

            if not existing_product:
                return "No data found"
            
            existing_product.product_category_id = form_data.product_category_id
            existing_product.visibility_id = form_data.visibility_id
            existing_product.code = form_data.code
            existing_product.description = form_data.description
            existing_product.min_stock = form_data.min_stock
            existing_product.max_stock = form_data.max_stock
            existing_product.measure = form_data.measure
            existing_product.balance = form_data.balance

            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def update_stock(self, product_id, quantity, operation):
        """
        Actualizar el stock de un producto
        operation: 'add' para sumar, 'subtract' para restar
        """
        try:
            product = self.db.query(ProductModel).filter(ProductModel.id == product_id).first()
            
            if not product:
                return {"status": "error", "message": f"Product with ID {product_id} not found"}
            
            if operation == "add":
                product.balance += quantity
            elif operation == "subtract":
                if product.balance < quantity:
                    return {"status": "error", "message": f"Insufficient stock for product {product.description}. Available: {product.balance}, Required: {quantity}"}
                product.balance -= quantity
            else:
                return {"status": "error", "message": "Invalid operation. Use 'add' or 'subtract'"}
            
            self.db.commit()
            return {"status": "success", "message": "Stock updated successfully", "new_balance": product.balance}
            
        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": f"Error updating stock: {error_message}"}