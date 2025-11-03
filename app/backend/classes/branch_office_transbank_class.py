from sqlalchemy.orm import Session
from app.backend.db.models import BranchOfficeTransbankViewModel, BranchOfficeModel, BranchOfficesTransbankStatementsModel
from fastapi import HTTPException
from sqlalchemy import text
import json

class BranchOfficeTransbankClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, page=1, items_per_page=10):
        """
        Obtiene todas las sucursales con información de Transbank activas (status_id = 7)
        """
        try:
            # Usar consulta SQL raw para obtener los datos según la consulta original
            query = """
            SELECT 
                bo.id AS id,
                bt.branch_office_id AS branch_office_id,
                bo.branch_office AS branch_office,
                bt.transbank_code AS codigo_comercio,
                bo.dte_code AS dte_code,
                bo.address AS address,
                r.region AS region,
                c.commune AS commune,
                (CASE WHEN bt.status = 0 THEN 'Activo' 
                      WHEN bt.status = 1 THEN 'Baja' 
                      ELSE 'Desconocido' END) AS status,
                CONCAT(u.name, ' ', u.last_name) AS responsable,
                bo.status_id AS status_id
            FROM branch_offices_transbanks bt
            LEFT JOIN branch_offices bo ON bt.branch_office_id = bo.id
            LEFT JOIN regions r ON bo.region_id = r.id
            LEFT JOIN communes c ON bo.commune_id = c.id
            LEFT JOIN users u ON bo.principal_supervisor = u.rut
            WHERE bo.status_id = 7
            ORDER BY bo.branch_office ASC
            """

            # Si se solicita paginación
            if page > 0:
                # Primero contar el total
                count_query = """
                SELECT COUNT(*) as total
                FROM branch_offices_transbanks bt
                LEFT JOIN branch_offices bo ON bt.branch_office_id = bo.id
                WHERE bo.status_id = 7
                """
                
                total_result = self.db.execute(text(count_query)).fetchone()
                total_items = total_result.total if total_result else 0
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                # Aplicar paginación
                offset = (page - 1) * items_per_page
                paginated_query = query + f" LIMIT {items_per_page} OFFSET {offset}"
                
                result = self.db.execute(text(paginated_query)).fetchall()

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
                        "responsable": row.responsable,
                        "status_id": row.status_id
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
                result = self.db.execute(text(query)).fetchall()

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
                        "responsable": row.responsable,
                        "status_id": row.status_id
                    })

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}

    def get_by_id(self, id: int):
        """
        Obtiene una sucursal específica por ID
        """
        try:
            query = """
            SELECT 
                bo.id AS id,
                bt.branch_office_id AS branch_office_id,
                bo.branch_office AS branch_office,
                bt.transbank_code AS codigo_comercio,
                bo.dte_code AS dte_code,
                bo.address AS address,
                r.region AS region,
                c.commune AS commune,
                (CASE WHEN bt.status = 0 THEN 'Activo' 
                      WHEN bt.status = 1 THEN 'Baja' 
                      ELSE 'Desconocido' END) AS status,
                CONCAT(u.name, ' ', u.last_name) AS responsable,
                bo.status_id AS status_id
            FROM branch_offices_transbanks bt
            LEFT JOIN branch_offices bo ON bt.branch_office_id = bo.id
            LEFT JOIN regions r ON bo.region_id = r.id
            LEFT JOIN communes c ON bo.commune_id = c.id
            LEFT JOIN users u ON bo.principal_supervisor = u.rut
            WHERE bo.id = :id AND bo.status_id = 7
            """

            result = self.db.execute(text(query), {"id": id}).fetchone()

            if result:
                return {
                    "id": result.id,
                    "branch_office_id": result.branch_office_id,
                    "branch_office": result.branch_office,
                    "codigo_comercio": result.codigo_comercio,
                    "dte_code": result.dte_code,
                    "address": result.address,
                    "region": result.region,
                    "commune": result.commune,
                    "status": result.status,
                    "responsable": result.responsable,
                    "status_id": result.status_id
                }
            else:
                return {"status": "error", "message": "Branch office not found"}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def search(self, branch_office=None, codigo_comercio=None, status=None, page=1, items_per_page=10):
        """
        Busca sucursales con filtros opcionales
        """
        try:
            base_query = """
            SELECT 
                bo.id AS id,
                bt.branch_office_id AS branch_office_id,
                bo.branch_office AS branch_office,
                bt.transbank_code AS codigo_comercio,
                bo.dte_code AS dte_code,
                bo.address AS address,
                r.region AS region,
                c.commune AS commune,
                (CASE WHEN bt.status = 0 THEN 'Activo' 
                      WHEN bt.status = 1 THEN 'Baja' 
                      ELSE 'Desconocido' END) AS status,
                CONCAT(u.name, ' ', u.last_name) AS responsable,
                bo.status_id AS status_id
            FROM branch_offices_transbanks bt
            LEFT JOIN branch_offices bo ON bt.branch_office_id = bo.id
            LEFT JOIN regions r ON bo.region_id = r.id
            LEFT JOIN communes c ON bo.commune_id = c.id
            LEFT JOIN users u ON bo.principal_supervisor = u.rut
            WHERE bo.status_id = 7
            """

            conditions = []
            params = {}

            if branch_office:
                conditions.append("bo.branch_office LIKE :branch_office")
                params["branch_office"] = f"%{branch_office}%"

            if codigo_comercio:
                conditions.append("bt.transbank_code LIKE :codigo_comercio")
                params["codigo_comercio"] = f"%{codigo_comercio}%"

            if status is not None:
                conditions.append("bt.status = :status")
                params["status"] = 0 if status.lower() == 'activo' else 1

            if conditions:
                base_query += " AND " + " AND ".join(conditions)

            base_query += " ORDER BY bo.branch_office ASC"

            # Contar total para paginación
            count_query = base_query.replace(
                "SELECT bo.id AS id, bt.branch_office_id AS branch_office_id, bo.branch_office AS branch_office, bt.transbank_code AS codigo_comercio, bo.dte_code AS dte_code, bo.address AS address, r.region AS region, c.commune AS commune, (CASE WHEN bt.status = 0 THEN 'Activo' WHEN bt.status = 1 THEN 'Baja' ELSE 'Desconocido' END) AS status, CONCAT(u.name, ' ', u.last_name) AS responsable, bo.status_id AS status_id",
                "SELECT COUNT(*) as total"
            ).split("ORDER BY")[0]

            total_result = self.db.execute(text(count_query), params).fetchone()
            total_items = total_result.total if total_result else 0
            total_pages = (total_items + items_per_page - 1) // items_per_page

            if page < 1 or page > total_pages:
                return {"status": "error", "message": "Invalid page number"}

            # Aplicar paginación
            offset = (page - 1) * items_per_page
            paginated_query = base_query + f" LIMIT {items_per_page} OFFSET {offset}"

            result = self.db.execute(text(paginated_query), params).fetchall()

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
                    "responsable": row.responsable,
                    "status_id": row.status_id
                })

            return {
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "items_per_page": items_per_page,
                "data": serialized_data
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def update_transbank_status(self, branch_office_id: int, status: int):
        """
        Actualiza el status de Transbank para una sucursal
        """
        try:
            transbank_record = self.db.query(BranchOfficesTransbankStatementsModel).filter(
                BranchOfficesTransbankStatementsModel.branch_office_id == branch_office_id
            ).first()

            if not transbank_record:
                raise HTTPException(status_code=404, detail="Transbank record not found")

            transbank_record.status = status
            self.db.commit()
            self.db.refresh(transbank_record)

            return {
                "status": "success",
                "message": "Transbank status updated successfully",
                "data": {
                    "branch_office_id": branch_office_id,
                    "new_status": "Activo" if status == 0 else "Baja"
                }
            }

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}
