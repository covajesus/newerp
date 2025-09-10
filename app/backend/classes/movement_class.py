from app.backend.db.models import MovementModel, MovementProductModel, ProductModel, BranchOfficeModel, SupplierModel
from app.backend.classes.product_class import ProductClass
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from datetime import datetime
import json

class MovementClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, page=0, items_per_page=10, movement_type=None, branch_office_id=None, 
                supplier_id=None, date_from=None, date_to=None):
        """
        Obtiene todos los movimientos con paginación y filtros opcionales
        """
        try:
            filters = []
            
            if movement_type:
                filters.append(MovementModel.movement_type == movement_type)
            
            if branch_office_id is not None:
                filters.append(MovementModel.branch_office_id == branch_office_id)
            
            if supplier_id is not None:
                filters.append(MovementModel.supplier_id == supplier_id)
            
            if date_from:
                filters.append(MovementModel.movement_date >= date_from)
            
            if date_to:
                filters.append(MovementModel.movement_date <= date_to)

            query = self.db.query(
                MovementModel.movement_id,
                MovementModel.movement_type,
                MovementModel.reference_number,
                MovementModel.description,
                MovementModel.total_amount,
                MovementModel.branch_office_id,
                MovementModel.supplier_id,
                MovementModel.user_rut,
                MovementModel.status_id,
                func.date_format(MovementModel.movement_date, "%d-%m-%Y %H:%i:%s").label("movement_date"),
                func.date_format(MovementModel.created_at, "%d-%m-%Y %H:%i:%s").label("created_date"),
                BranchOfficeModel.branch_office.label("branch_office_name"),
                SupplierModel.supplier.label("supplier_name")
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == MovementModel.branch_office_id
            ).outerjoin(
                SupplierModel, SupplierModel.id == MovementModel.supplier_id
            ).filter(
                *filters
            ).order_by(
                MovementModel.movement_id.desc()
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
                    "movement_id": movement.movement_id,
                    "movement_type": movement.movement_type,
                    "reference_number": movement.reference_number,
                    "description": movement.description,
                    "total_amount": movement.total_amount,
                    "branch_office_id": movement.branch_office_id,
                    "branch_office_name": movement.branch_office_name,
                    "supplier_id": movement.supplier_id,
                    "supplier_name": movement.supplier_name,
                    "user_rut": movement.user_rut,
                    "status_id": movement.status_id,
                    "movement_date": movement.movement_date,
                    "created_date": movement.created_date
                } for movement in data]

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
                    "movement_id": movement.movement_id,
                    "movement_type": movement.movement_type,
                    "reference_number": movement.reference_number,
                    "description": movement.description,
                    "total_amount": movement.total_amount,
                    "branch_office_id": movement.branch_office_id,
                    "branch_office_name": movement.branch_office_name,
                    "supplier_id": movement.supplier_id,
                    "supplier_name": movement.supplier_name,
                    "user_rut": movement.user_rut,
                    "status_id": movement.status_id,
                    "movement_date": movement.movement_date,
                    "created_date": movement.created_date
                } for movement in data]

                return serialized_data

        except Exception as e:
            return {"status": "error", "message": f"Error retrieving movements: {str(e)}"}

    def get(self, movement_id):
        """
        Obtiene un movimiento específico con sus productos
        """
        try:
            # Obtener datos del movimiento
            movement_query = self.db.query(
                MovementModel.movement_id,
                MovementModel.movement_type,
                MovementModel.reference_number,
                MovementModel.description,
                MovementModel.total_amount,
                MovementModel.branch_office_id,
                MovementModel.supplier_id,
                MovementModel.user_rut,
                MovementModel.status_id,
                func.date_format(MovementModel.movement_date, "%d-%m-%Y %H:%i:%s").label("movement_date"),
                func.date_format(MovementModel.created_at, "%d-%m-%Y %H:%i:%s").label("created_date"),
                BranchOfficeModel.branch_office.label("branch_office_name"),
                SupplierModel.supplier.label("supplier_name")
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == MovementModel.branch_office_id
            ).outerjoin(
                SupplierModel, SupplierModel.id == MovementModel.supplier_id
            ).filter(
                MovementModel.movement_id == movement_id
            ).first()

            if not movement_query:
                return {"status": "error", "message": "Movement not found"}

            # Obtener productos del movimiento
            products_query = self.db.query(
                MovementProductModel.movement_product_id,
                MovementProductModel.product_id,
                MovementProductModel.cost,
                MovementProductModel.qty,
                ProductModel.name.label("product_name"),
                ProductModel.description.label("product_description"),
                ProductModel.barcode.label("product_barcode")
            ).join(
                ProductModel, ProductModel.product_id == MovementProductModel.product_id
            ).filter(
                MovementProductModel.movement_id == movement_id
            ).all()

            movement_data = {
                "movement_id": movement_query.movement_id,
                "movement_type": movement_query.movement_type,
                "reference_number": movement_query.reference_number,
                "description": movement_query.description,
                "total_amount": movement_query.total_amount,
                "branch_office_id": movement_query.branch_office_id,
                "branch_office_name": movement_query.branch_office_name,
                "supplier_id": movement_query.supplier_id,
                "supplier_name": movement_query.supplier_name,
                "user_rut": movement_query.user_rut,
                "status_id": movement_query.status_id,
                "movement_date": movement_query.movement_date,
                "created_date": movement_query.created_date,
                "products": [{
                    "movement_product_id": product.movement_product_id,
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "product_description": product.product_description,
                    "product_barcode": product.product_barcode,
                    "cost": product.cost,
                    "qty": product.qty,
                    "subtotal": product.cost * product.qty
                } for product in products_query]
            }

            return {"status": "success", "data": movement_data}

        except Exception as e:
            return {"status": "error", "message": f"Error retrieving movement: {str(e)}"}

    def store(self, form_data):
        """
        Crear un nuevo movimiento con productos
        """
        try:
            # Calcular total
            total_amount = 0
            for product in form_data.products:
                total_amount += product.cost * product.qty

            # Crear movimiento
            new_movement = MovementModel(
                movement_type=form_data.movement_type,
                reference_number=form_data.reference_number,
                description=form_data.description,
                total_amount=total_amount,
                branch_office_id=form_data.branch_office_id,
                supplier_id=form_data.supplier_id,
                user_rut=form_data.user_rut,
                status_id=form_data.status_id or 1,
                movement_date=datetime.strptime(form_data.movement_date, "%Y-%m-%d %H:%M:%S") if form_data.movement_date else datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(new_movement)
            self.db.commit()
            self.db.refresh(new_movement)

            # Crear productos del movimiento y actualizar stock
            product_class = ProductClass(self.db)
            
            for product_data in form_data.products:
                # Crear registro en movements_products
                movement_product = MovementProductModel(
                    product_id=product_data.product_id,
                    movement_id=new_movement.movement_id,
                    cost=product_data.cost,
                    qty=product_data.qty,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                self.db.add(movement_product)
                
                # Actualizar stock según el tipo de movimiento
                if form_data.movement_type == "IN":
                    # Entrada: sumar al stock
                    product_class.update_stock(product_data.product_id, product_data.qty, "add")
                elif form_data.movement_type == "OUT":
                    # Salida: restar del stock
                    stock_result = product_class.update_stock(product_data.product_id, product_data.qty, "subtract")
                    if stock_result["status"] == "error":
                        self.db.rollback()
                        return stock_result

            self.db.commit()

            return {"status": "success", "message": "Movement created successfully", "movement_id": new_movement.movement_id}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error creating movement: {str(e)}"}

    def update(self, movement_id, form_data):
        """
        Actualizar un movimiento existente
        """
        try:
            movement = self.db.query(MovementModel).filter(
                MovementModel.movement_id == movement_id
            ).first()

            if not movement:
                return {"status": "error", "message": "Movement not found"}

            # Actualizar campos del movimiento
            if form_data.movement_type is not None:
                movement.movement_type = form_data.movement_type
            if form_data.reference_number is not None:
                movement.reference_number = form_data.reference_number
            if form_data.description is not None:
                movement.description = form_data.description
            if form_data.branch_office_id is not None:
                movement.branch_office_id = form_data.branch_office_id
            if form_data.supplier_id is not None:
                movement.supplier_id = form_data.supplier_id
            if form_data.user_rut is not None:
                movement.user_rut = form_data.user_rut
            if form_data.status_id is not None:
                movement.status_id = form_data.status_id
            if form_data.movement_date is not None:
                movement.movement_date = datetime.strptime(form_data.movement_date, "%Y-%m-%d %H:%M:%S")

            movement.updated_at = datetime.utcnow()

            self.db.commit()

            return {"status": "success", "message": "Movement updated successfully"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error updating movement: {str(e)}"}

    def delete(self, movement_id):
        """
        Eliminar un movimiento (cambiar status_id a 0) y revertir cambios de stock
        """
        try:
            movement = self.db.query(MovementModel).filter(
                MovementModel.movement_id == movement_id
            ).first()

            if not movement:
                return {"status": "error", "message": "Movement not found"}

            # Obtener productos del movimiento para revertir stock
            movement_products = self.db.query(MovementProductModel).filter(
                MovementProductModel.movement_id == movement_id
            ).all()

            product_class = ProductClass(self.db)
            
            # Revertir cambios de stock
            for movement_product in movement_products:
                if movement.movement_type == "IN":
                    # Si fue entrada, restar del stock
                    product_class.update_stock(movement_product.product_id, movement_product.qty, "subtract")
                elif movement.movement_type == "OUT":
                    # Si fue salida, sumar al stock
                    product_class.update_stock(movement_product.product_id, movement_product.qty, "add")

            # Marcar movimiento como eliminado
            movement.status_id = 0
            movement.updated_at = datetime.utcnow()

            self.db.commit()

            return {"status": "success", "message": "Movement deleted successfully and stock reverted"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error deleting movement: {str(e)}"}

    def get_movement_products(self, movement_id):
        """
        Obtiene los productos de un movimiento específico
        """
        try:
            products_query = self.db.query(
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
            ).all()

            if not products_query:
                return {"status": "error", "message": "No products found for this movement"}

            products_data = [{
                "movement_product_id": product.movement_product_id,
                "product_id": product.product_id,
                "product_name": product.product_name,
                "product_description": product.product_description,
                "product_barcode": product.product_barcode,
                "cost": product.cost,
                "qty": product.qty,
                "subtotal": product.cost * product.qty,
                "current_stock": product.current_stock
            } for product in products_query]

            return {"status": "success", "data": products_data}

        except Exception as e:
            return {"status": "error", "message": f"Error retrieving movement products: {str(e)}"}
