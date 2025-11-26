from app.backend.db.models import MovementProductModel, ProductModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime
import json

class MovementProductClass:
    def __init__(self, db: Session):
        self.db = db

    def show(self, movement_id: int, page: int = 1, items_per_page: int = 10):
        try:
            # Construir la consulta equivalente al PHP
            query = self.db.query(
                MovementProductModel.movement_product_id.label("movement_product_id"),
                ProductModel.barcode.label("code"),  # Usando barcode como 'code' ya que no hay campo 'code' en la estructura SQL
                ProductModel.description.label("description"),
                MovementProductModel.qty.label("quantity"),
                MovementProductModel.cost.label("cost")
            ).outerjoin(
                ProductModel, ProductModel.product_id == MovementProductModel.product_id
            ).filter(
                MovementProductModel.movement_id == movement_id
            ).order_by(
                desc(ProductModel.description)
            )

            # Aplicar paginación
            if page > 0:
                total_items = query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No movement products found"}

                serialized_data = [{
                    "movement_product_id": item.movement_product_id,
                    "code": item.code,
                    "description": item.description,
                    "quantity": item.quantity,
                    "cost": item.cost
                } for item in data]

                return {
                    "status": "success",
                    "data": serialized_data,
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page
                }
            else:
                # Sin paginación
                data = query.all()
                
                serialized_data = [{
                    "movement_product_id": item.movement_product_id,
                    "code": item.code,
                    "description": item.description,
                    "quantity": item.quantity,
                    "cost": item.cost
                } for item in data]

                return {
                    "status": "success",
                    "data": serialized_data
                }

        except Exception as e:
            return {"status": "error", "message": f"Error retrieving movement products: {str(e)}"}

    def get_all(self, movement_id: int):
        """
        Obtener todos los productos de un movimiento sin paginación
        """
        try:
            data = self.db.query(
                MovementProductModel.movement_product_id,
                MovementProductModel.product_id,
                MovementProductModel.cost,
                MovementProductModel.qty,
                ProductModel.name.label("product_name"),
                ProductModel.description.label("product_description"),
                ProductModel.barcode.label("product_barcode"),
                ProductModel.stock.label("current_stock")
            ).join(
                ProductModel, ProductModel.product_id == MovementProductModel.product_id
            ).filter(
                MovementProductModel.movement_id == movement_id
            ).order_by(
                desc(ProductModel.description)
            ).all()

            if not data:
                return {"status": "error", "message": "No products found for this movement"}

            serialized_data = [{
                "movement_product_id": item.movement_product_id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "product_description": item.product_description,
                "product_barcode": item.product_barcode,
                "cost": item.cost,
                "qty": item.qty,
                "subtotal": item.cost * item.qty,
                "current_stock": item.current_stock
            } for item in data]

            return {"status": "success", "data": serialized_data}

        except Exception as e:
            return {"status": "error", "message": f"Error retrieving movement products: {str(e)}"}

    def get(self, movement_product_id: int):
        """
        Obtener un producto específico de un movimiento
        """
        try:
            data = self.db.query(
                MovementProductModel.movement_product_id,
                MovementProductModel.product_id,
                MovementProductModel.movement_id,
                MovementProductModel.cost,
                MovementProductModel.qty,
                func.date_format(MovementProductModel.created_at, "%d-%m-%Y %H:%i:%s").label("created_date"),
                ProductModel.name.label("product_name"),
                ProductModel.description.label("product_description"),
                ProductModel.barcode.label("product_barcode")
            ).join(
                ProductModel, ProductModel.product_id == MovementProductModel.product_id
            ).filter(
                MovementProductModel.movement_product_id == movement_product_id
            ).first()

            if not data:
                return {"status": "error", "message": "Movement product not found"}

            movement_product_data = {
                "movement_product_id": data.movement_product_id,
                "product_id": data.product_id,
                "movement_id": data.movement_id,
                "product_name": data.product_name,
                "product_description": data.product_description,
                "product_barcode": data.product_barcode,
                "cost": data.cost,
                "qty": data.qty,
                "subtotal": data.cost * data.qty,
                "created_date": data.created_date
            }

            return {"status": "success", "data": movement_product_data}

        except Exception as e:
            return {"status": "error", "message": f"Error retrieving movement product: {str(e)}"}
