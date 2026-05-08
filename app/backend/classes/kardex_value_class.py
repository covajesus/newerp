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
        Actualizar kardex. El campo ``cost`` en BD es la valorización total del inventario
        (costo total acumulado), coherente con el frontend (divide por cantidad para el unitario).

        qty_change: positivo entradas, negativo salidas
        new_cost: en entrada, costo unitario del lote; en salida, costo total de la línea a dar de baja.
                  Salida con 0: se usa (cantidad salida) × (valor total / cantidad actual).
        """
        try:
            # Obtener el registro actual del kardex para este producto
            current_kardex = self.db.query(KardexValueModel).filter(
                KardexValueModel.product_id == product_id
            ).first()
            
            if current_kardex:
                current_qty = current_kardex.qty or 0
                current_total_valuation = current_kardex.cost or 0
                
                new_qty_total = current_qty + qty_change
                
                if qty_change < 0:
                    # Salida: restar el costo total de línea del valor total en kardex (no qty × cost).
                    explicit_line_total = int(round(float(new_cost))) if new_cost is not None else 0
                    if explicit_line_total > 0:
                        line_total = explicit_line_total
                    elif current_qty > 0:
                        unit_val = int(current_total_valuation / current_qty)
                        line_total = abs(qty_change) * unit_val
                    else:
                        line_total = 0
                    new_total_valuation = max(0, current_total_valuation - line_total)
                    new_qty_total = max(0, new_qty_total)
                    if new_qty_total <= 0:
                        new_qty_total = 0
                        new_total_valuation = 0
                    current_kardex.qty = new_qty_total
                    current_kardex.cost = new_total_valuation
                elif qty_change > 0:
                    # Entrada: sumar valor comprado (costo unitario × cantidad) al total en kardex
                    if new_qty_total <= 0:
                        current_kardex.qty = max(0, new_qty_total)
                        current_kardex.cost = current_total_valuation
                    else:
                        unit_in = float(new_cost or 0)
                        added_value = int(round(unit_in * qty_change))
                        current_kardex.qty = new_qty_total
                        current_kardex.cost = current_total_valuation + added_value
                else:
                    pass
                
            else:
                # No existe registro previo - crear nuevo
                if qty_change > 0:
                    unit_in = float(new_cost or 0)
                    initial_total = int(round(unit_in * qty_change))
                    new_kardex = KardexValueModel(
                        product_id=product_id,
                        qty=max(0, qty_change),
                        cost=initial_total,
                    )
                else:
                    new_kardex = KardexValueModel(
                        product_id=product_id,
                        qty=0,
                        cost=0,
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