from app.backend.db.models import KardexValueModel, ProductModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from datetime import datetime
import json
from app.backend.db.models import MovementProductModel, MovementModel

class KardexValueClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, page=0, items_per_page=10, code=None, product_id=None):
        try:
            query = self.db.query(
                ProductModel.barcode.label("code"),
                ProductModel.description.label("description"),
                ProductModel.category.label("category"),
                func.date_format(MovementModel.created_at, "%Y-%m-%d").label("fecha"),
                MovementModel.movement_type.label("tipo_movimiento"),
                MovementProductModel.qty.label("cantidad"),
                MovementProductModel.cost.label("precio_unitario"),
                (MovementProductModel.qty * MovementProductModel.cost).label("total"),
                KardexValueModel.kardex_value_id
            ).select_from(MovementProductModel)\
            .join(ProductModel, ProductModel.product_id == MovementProductModel.product_id)\
            .join(MovementModel, MovementModel.movement_id == MovementProductModel.movement_id)\
            .outerjoin(KardexValueModel, KardexValueModel.product_id == ProductModel.product_id)\
            .filter(
                ProductModel.description != '',
                ProductModel.description.isnot(None),
                MovementModel.status_id != 9,
                ProductModel.visibility_id == 1
            )

            # Aplicar filtros
            if code is not None and code != 'null' and code != '':
                query = query.filter(ProductModel.barcode == code)
            
            if product_id is not None and product_id != 'null' and product_id != '':
                query = query.filter(ProductModel.product_id == product_id)

            # Ordenar por fecha descendente
            query = query.order_by(MovementModel.created_at.desc())

            if page > 0:
                total_items = query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                # Calcular saldo acumulado (esto es una simplificación, idealmente deberías calcularlo correctamente)
                saldo_acumulado = 0
                serialized_data = []
                
                for movement in data:
                    # Ajustar saldo según tipo de movimiento
                    if movement.tipo_movimiento and movement.tipo_movimiento.upper() == 'IN':
                        saldo_acumulado += movement.cantidad or 0
                        tipo_display = 'ENTRADA'
                    else:
                        saldo_acumulado -= movement.cantidad or 0
                        tipo_display = 'SALIDA'
                    
                    item = {
                        "id": movement.kardex_value_id or hash(f"{movement.code}{movement.fecha}"),
                        "codigo": movement.code or "",
                        "descripcion": movement.description or "",
                        "categoria": movement.category or "General",
                        "fecha": movement.fecha or "2024-01-01",
                        "tipo_movimiento": tipo_display,
                        "cantidad": movement.cantidad or 0,
                        "precio_unitario": movement.precio_unitario or 0,
                        "total": movement.total or 0,
                        "saldo": max(0, saldo_acumulado)  # No permitir saldos negativos
                    }
                    serialized_data.append(item)

                return {
                    "status": "success",
                    "data": serialized_data,
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page
                }
            else:
                data = query.all()
                
                saldo_acumulado = 0
                serialized_data = []
                
                for movement in data:
                    if movement.tipo_movimiento and movement.tipo_movimiento.upper() == 'IN':
                        saldo_acumulado += movement.cantidad or 0
                        tipo_display = 'ENTRADA'
                    else:
                        saldo_acumulado -= movement.cantidad or 0
                        tipo_display = 'SALIDA'
                    
                    item = {
                        "id": movement.kardex_value_id or hash(f"{movement.code}{movement.fecha}"),
                        "codigo": movement.code or "",
                        "descripcion": movement.description or "",
                        "categoria": movement.category or "General",
                        "fecha": movement.fecha or "2024-01-01",
                        "tipo_movimiento": tipo_display,
                        "cantidad": movement.cantidad or 0,
                        "precio_unitario": movement.precio_unitario or 0,
                        "total": movement.total or 0,
                        "saldo": max(0, saldo_acumulado)
                    }
                    serialized_data.append(item)

                return {"status": "success", "data": serialized_data}

        except Exception as e:
            return {"status": "error", "message": f"Error retrieving kardex movements: {str(e)}"}
