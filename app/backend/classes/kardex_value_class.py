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
            
            # Solo agregar JOINs si los filtros correspondientes están presentes
            if branch_office_id is not None or product_id is not None:
                # JOIN con MovementProductModel
                query = query.outerjoin(
                    MovementProductModel, MovementProductModel.product_id == ProductModel.id
                )
                
                # JOIN con MovementModel solo si necesitamos filtrar por branch_office
                if branch_office_id is not None:
                    query = query.outerjoin(
                        MovementModel, MovementModel.id == MovementProductModel.movement_id
                    )
            
            # Aplicar filtros dinámicos
            filters = []
            if branch_office_id is not None:
                filters.append(MovementModel.branch_office_id == branch_office_id)
            if product_id is not None:
                filters.append(MovementProductModel.product_id == product_id)
            if code is not None:
                filters.append(ProductModel.code == code)
            
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