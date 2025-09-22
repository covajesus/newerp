from app.backend.db.database import SessionLocal
from app.backend.db.models import ProductModel, MovementModel, MovementProductModel, KardexValueModel
from sqlalchemy.orm import Session

class KardexValueClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, code=None, product_id=None, branch_office_id=None, page=0, items_per_page=10):
        try:
            # Construir la consulta base
            query = self.db.query(
                KardexValueModel.qty,
                KardexValueModel.cost,
                ProductModel.id,
                ProductModel.code,
                ProductModel.description
            ).select_from(ProductModel)
            
            # JOIN con KardexValueModel
            query = query.outerjoin(
                KardexValueModel, KardexValueModel.product_id == ProductModel.id
            )
            
            # Aplicar filtros dinámicos
            filters = []
            if product_id is not None and product_id > 0:
                filters.append(ProductModel.id == product_id)
            if code is not None and code != "":
                filters.append(ProductModel.code == code)
            
            filters.append(ProductModel.visibility_id == 1)
            
            if filters:
                query = query.filter(*filters)
            
            # Agregar DISTINCT para evitar duplicados y ordenar
            query = query.distinct().order_by(ProductModel.description.asc())
            
            # Si se solicita paginación
            if page > 0:
                # Calcular el total de registros
                total_items = query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page
                
                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}
                
                # Aplicar paginación en la consulta
                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()
                
                if not data:
                    return {"status": "error", "message": "No data found"}
                
                # Serializar los datos
                serialized_data = [{
                    "id": row.id,
                    "code": row.code,
                    "description": row.description,
                    "quantity": row.qty,
                    "cost": row.cost
                } for row in data]

                print(serialized_data)

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }
            
            # Sin paginación - obtener todos los datos
            data = query.all()
            serialized_data = [{
                "id": row.id,
                "code": row.code,
                "description": row.description,
                "quantity": row.qty,
                "cost": row.cost
            } for row in data]
            
            return serialized_data
            
        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}

    def store_kardex_entry(self, product_id, qty_change, new_cost):
        """
        Crear/actualizar registro de kardex con costo promedio ponderado
        qty_change: cantidad a sumar o restar (positivo para entradas, negativo para salidas)
        new_cost: costo unitario del nuevo movimiento
        """
        try:
            # Obtener el registro actual del kardex para este producto
            current_kardex = self.db.query(KardexValueModel).filter(
                KardexValueModel.product_id == product_id
            ).first()
            
            if current_kardex:
                # Existe registro previo - calcular costo promedio ponderado
                current_qty = current_kardex.qty or 0
                current_cost = current_kardex.cost or 0
                
                # Nueva cantidad total
                new_qty_total = current_qty + qty_change
                
                if new_qty_total <= 0:
                    # Si la cantidad queda en 0 o negativa, mantener costo actual
                    new_avg_cost = current_cost
                    new_qty_total = max(0, new_qty_total)  # No permitir cantidades negativas
                else:
                    # Calcular costo promedio ponderado
                    # (costo_anterior * qty_anterior + costo_nuevo * qty_cambio) / qty_total_nueva
                    if qty_change > 0:  # Solo para entradas (aumentos de stock)
                        total_cost_value = (current_cost * current_qty) + (new_cost * qty_change)
                        new_avg_cost = int(total_cost_value / new_qty_total)
                    else:  # Para salidas, mantener el costo promedio actual
                        new_avg_cost = current_cost
                
                # Actualizar registro existente
                current_kardex.qty = new_qty_total
                current_kardex.cost = new_avg_cost
                
            else:
                # No existe registro previo - crear nuevo
                new_kardex = KardexValueModel(
                    product_id=product_id,
                    qty=max(0, qty_change),  # No permitir cantidades negativas
                    cost=new_cost if qty_change > 0 else 0
                )
                self.db.add(new_kardex)
            
            self.db.commit()
            return {"status": "success", "message": "Kardex updated successfully"}
            
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error updating kardex: {str(e)}"}

    def get_by_product_id(self, product_id):
        """
        Obtener los datos de kardex por product_id
        """
        try:
            # Consultar kardex y datos del producto
            result = self.db.query(
                KardexValueModel.qty,
                KardexValueModel.cost,
                ProductModel.id,
                ProductModel.code,
                ProductModel.description
            ).select_from(ProductModel).outerjoin(
                KardexValueModel, KardexValueModel.product_id == ProductModel.id
            ).filter(
                ProductModel.id == product_id
            ).first()
            
            if not result:
                return {"status": "error", "message": "Product not found"}
            
            return {
                "status": "success",
                "data": {
                    "id": result.id,
                    "code": result.code,
                    "description": result.description,
                    "quantity": result.qty if result.qty is not None else 0,
                    "cost": result.cost if result.cost is not None else 0
                }
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Error retrieving kardex data: {str(e)}"}