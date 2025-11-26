from sqlalchemy.orm import Session
from app.backend.db.models import TransbankDataModel

class BranchOfficeTransbankClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, page=1, items_per_page=10, branch_office_id=None):
        try:
            query = self.db.query(
                TransbankDataModel.id,
                TransbankDataModel.branch_office_id,
                TransbankDataModel.branch_office,
                TransbankDataModel.codigo_comercio,
                TransbankDataModel.dte_code,
                TransbankDataModel.address,
                TransbankDataModel.region,
                TransbankDataModel.commune,
                TransbankDataModel.status,
                TransbankDataModel.responsable
            )

            # Aplicar filtro por branch_office_id si se proporciona
            if branch_office_id is not None:
                query = query.filter(TransbankDataModel.branch_office_id == branch_office_id)

            # Si se solicita paginación
            if page > 0:
                # Contar el total de registros
                total_items = query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or (total_pages > 0 and page > total_pages):
                    return {"status": "error", "message": "Invalid page number"}

                # Aplicar paginación
                result = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                # Serializar los datos
                serialized_data = []
                for row in result:
                    serialized_data.append({
                        "id": row.id,
                        "branch_office_id": row.branch_office_id,
                        "branch_office": row.branch_office,
                        "codigo_comercio": row.codigo_comercio,
                        "dte_code": row.dte_code,
                        "address": row.address,
                        "region": row.region,
                        "commune": row.commune,
                        "status": row.status,
                        "responsable": row.responsable
                    })

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }
            else:
                # Sin paginación, traer todos
                result = query.all()

                serialized_data = []
                for row in result:
                    serialized_data.append({
                        "id": row.id,
                        "branch_office_id": row.branch_office_id,
                        "branch_office": row.branch_office,
                        "codigo_comercio": row.codigo_comercio,
                        "dte_code": row.dte_code,
                        "address": row.address,
                        "region": row.region,
                        "commune": row.commune,
                        "status": row.status,
                        "responsable": row.responsable
                    })

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}