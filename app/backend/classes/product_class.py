from app.backend.db.models import ProductModel, SupplierModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from datetime import datetime
import json

class ProductClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, page=0, items_per_page=10, search=None, category_id=None, supplier_id=None):
        """
        Obtiene todos los productos con paginación y filtros opcionales
        """
        try:
            filters = []
            
            if search:
                filters.append(or_(
                    ProductModel.name.contains(search),
                    ProductModel.description.contains(search),
                    ProductModel.barcode.contains(search)
                ))
            
            if category_id is not None:
                filters.append(ProductModel.category_id == category_id)
            
            if supplier_id is not None:
                filters.append(ProductModel.supplier_id == supplier_id)

            query = self.db.query(
                ProductModel.product_id,
                ProductModel.name,
                ProductModel.description,
                ProductModel.cost,
                ProductModel.price,
                ProductModel.stock,
                ProductModel.category_id,
                ProductModel.supplier_id,
                ProductModel.brand,
                ProductModel.model,
                ProductModel.barcode,
                ProductModel.status_id,
                func.date_format(ProductModel.created_at, "%d-%m-%Y %H:%i:%s").label("created_date"),
                SupplierModel.supplier.label("supplier_name")
            ).outerjoin(
                SupplierModel, SupplierModel.id == ProductModel.supplier_id
            ).filter(
                *filters
            ).order_by(
                ProductModel.product_id.desc()
            )

            if page > 0:
                total_items = query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                serialized_data = [{
                    "product_id": product.product_id,
                    "name": product.name,
                    "description": product.description,
                    "cost": product.cost,
                    "price": product.price,
                    "stock": product.stock,
                    "category_id": product.category_id,
                    "supplier_id": product.supplier_id,
                    "supplier_name": product.supplier_name,
                    "brand": product.brand,
                    "model": product.model,
                    "barcode": product.barcode,
                    "status_id": product.status_id,
                    "created_date": product.created_date
                } for product in data]

                return {
                    "status": "success",
                    "data": serialized_data,
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page
                }
            else:
                data = query.all()
                
                serialized_data = [{
                    "product_id": product.product_id,
                    "name": product.name,
                    "description": product.description,
                    "cost": product.cost,
                    "price": product.price,
                    "stock": product.stock,
                    "category_id": product.category_id,
                    "supplier_id": product.supplier_id,
                    "supplier_name": product.supplier_name,
                    "brand": product.brand,
                    "model": product.model,
                    "barcode": product.barcode,
                    "status_id": product.status_id,
                    "created_date": product.created_date
                } for product in data]

                return serialized_data

        except Exception as e:
            return {"status": "error", "message": f"Error retrieving products: {str(e)}"}

    def get(self, product_id):
        """
        Obtiene un producto específico por ID
        """
        try:
            data_query = self.db.query(
                ProductModel.product_id,
                ProductModel.name,
                ProductModel.description,
                ProductModel.cost,
                ProductModel.price,
                ProductModel.stock,
                ProductModel.category_id,
                ProductModel.supplier_id,
                ProductModel.brand,
                ProductModel.model,
                ProductModel.barcode,
                ProductModel.status_id,
                func.date_format(ProductModel.created_at, "%d-%m-%Y %H:%i:%s").label("created_date"),
                SupplierModel.supplier.label("supplier_name")
            ).outerjoin(
                SupplierModel, SupplierModel.id == ProductModel.supplier_id
            ).filter(
                ProductModel.product_id == product_id
            ).first()

            if data_query:
                product_data = {
                    "product_id": data_query.product_id,
                    "name": data_query.name,
                    "description": data_query.description,
                    "cost": data_query.cost,
                    "price": data_query.price,
                    "stock": data_query.stock,
                    "category_id": data_query.category_id,
                    "supplier_id": data_query.supplier_id,
                    "supplier_name": data_query.supplier_name,
                    "brand": data_query.brand,
                    "model": data_query.model,
                    "barcode": data_query.barcode,
                    "status_id": data_query.status_id,
                    "created_date": data_query.created_date
                }

                return {"status": "success", "data": product_data}
            else:
                return {"status": "error", "message": "Product not found"}

        except Exception as e:
            return {"status": "error", "message": f"Error retrieving product: {str(e)}"}

    def store(self, form_data):
        """
        Crear un nuevo producto
        """
        try:
            # Verificar si ya existe un producto con el mismo código de barras
            if form_data.barcode:
                existing_product = self.db.query(ProductModel).filter(
                    ProductModel.barcode == form_data.barcode
                ).first()
                
                if existing_product:
                    return {"status": "error", "message": "A product with this barcode already exists"}

            new_product = ProductModel(
                name=form_data.name,
                description=form_data.description,
                cost=form_data.cost,
                price=form_data.price,
                stock=form_data.stock or 0,
                category_id=form_data.category_id,
                supplier_id=form_data.supplier_id,
                brand=form_data.brand,
                model=form_data.model,
                barcode=form_data.barcode,
                status_id=form_data.status_id or 1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(new_product)
            self.db.commit()
            self.db.refresh(new_product)

            return {"status": "success", "message": "Product created successfully", "product_id": new_product.product_id}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error creating product: {str(e)}"}

    def update(self, product_id, form_data):
        """
        Actualizar un producto existente
        """
        try:
            product = self.db.query(ProductModel).filter(
                ProductModel.product_id == product_id
            ).first()

            if not product:
                return {"status": "error", "message": "Product not found"}

            # Verificar código de barras duplicado (excluyendo el producto actual)
            if form_data.barcode and form_data.barcode != product.barcode:
                existing_product = self.db.query(ProductModel).filter(
                    ProductModel.barcode == form_data.barcode,
                    ProductModel.product_id != product_id
                ).first()
                
                if existing_product:
                    return {"status": "error", "message": "A product with this barcode already exists"}

            # Actualizar campos
            if form_data.name is not None:
                product.name = form_data.name
            if form_data.description is not None:
                product.description = form_data.description
            if form_data.cost is not None:
                product.cost = form_data.cost
            if form_data.price is not None:
                product.price = form_data.price
            if form_data.stock is not None:
                product.stock = form_data.stock
            if form_data.category_id is not None:
                product.category_id = form_data.category_id
            if form_data.supplier_id is not None:
                product.supplier_id = form_data.supplier_id
            if form_data.brand is not None:
                product.brand = form_data.brand
            if form_data.model is not None:
                product.model = form_data.model
            if form_data.barcode is not None:
                product.barcode = form_data.barcode
            if form_data.status_id is not None:
                product.status_id = form_data.status_id

            product.updated_at = datetime.utcnow()

            self.db.commit()

            return {"status": "success", "message": "Product updated successfully"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error updating product: {str(e)}"}

    def delete(self, product_id):
        """
        Eliminar un producto (cambiar status_id a 0)
        """
        try:
            product = self.db.query(ProductModel).filter(
                ProductModel.product_id == product_id
            ).first()

            if not product:
                return {"status": "error", "message": "Product not found"}

            product.status_id = 0
            product.updated_at = datetime.utcnow()

            self.db.commit()

            return {"status": "success", "message": "Product deleted successfully"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error deleting product: {str(e)}"}

    def update_stock(self, product_id, quantity, operation="add"):
        """
        Actualizar el stock de un producto
        operation: "add" para sumar, "subtract" para restar
        """
        try:
            product = self.db.query(ProductModel).filter(
                ProductModel.product_id == product_id
            ).first()

            if not product:
                return {"status": "error", "message": "Product not found"}

            if operation == "add":
                product.stock += quantity
            elif operation == "subtract":
                if product.stock < quantity:
                    return {"status": "error", "message": "Insufficient stock"}
                product.stock -= quantity
            else:
                return {"status": "error", "message": "Invalid operation. Use 'add' or 'subtract'"}

            product.updated_at = datetime.utcnow()
            self.db.commit()

            return {"status": "success", "message": f"Stock updated. New stock: {product.stock}"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error updating stock: {str(e)}"}
