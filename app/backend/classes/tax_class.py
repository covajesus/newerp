from datetime import datetime
from sqlalchemy.orm import Session
from app.backend.db.models import TaxModel
from datetime import datetime

class TaxClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, month=None, year=None, page=0, items_per_page=10):
        try:
            # Inicialización de la variable data_query
            data_query = None

            # Comprobamos si la página es distinta de 0 y filtramos por sucursal si se proporciona el ID
            if page != 0:
                if month is not None and year is not None:
                    # Incluir la información de la sucursal (BranchOfficeModel)
                    data_query = self.db.query(TaxModel.id, TaxModel.month, TaxModel.year). \
                        filter(TaxModel.month == month). \
                        filter(TaxModel.year == year). \
                        order_by(TaxModel.id)
                else:
                    data_query = self.db.query(TaxModel.id, TaxModel.month, TaxModel.year). \
                        order_by(TaxModel.id)

                # Si data_query ha sido definida, realizamos la paginación
                if data_query:
                    total_items = data_query.count()
                    total_pages = (total_items + items_per_page - 1) // items_per_page

                    if page < 1 or page > total_pages:
                        return {"status": "error", "message": "Invalid page number"}

                    data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                    if not data:
                        return {"status": "error", "message": "No data found"}

                    serialized_data = [{
                        "id": tax.id,
                        "month": tax.month,
                        "year": tax.year
                    } for tax in data]  # Solo iteramos sobre los contratos

                    return {
                        "total_items": total_items,
                        "total_pages": total_pages,
                        "current_page": page,
                        "items_per_page": items_per_page,
                        "data": serialized_data
                    }

            # Si la página es 0, traer todos los registros sin paginación
            else:
                if month is not None and year is not None:
                    data_query = self.db.query(TaxModel.id, TaxModel.month, TaxModel.year). \
                        filter(TaxModel.month == month). \
                        filter(TaxModel.year == year). \
                        order_by(TaxModel.rut).all()
                else:
                    data_query = self.db.query(TaxModel.id, TaxModel.month, TaxModel.year). \
                        order_by(TaxModel.rut).all()

                # Serializar los datos y formatear las fechas
                serialized_data = [{
                    "id": tax.id,
                    "month": tax.month,
                    "year": tax.year,
                } for tax in data_query]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}



    def store(self, form_data, support):
        # Crear una nueva instancia de ContractModel
        tax = TaxModel()
        
        # Asignar los valores del formulario a la instancia del modelo
        tax.month = form_data.month
        tax.year = form_data.year

        # Añadir la nueva instancia a la base de datos
        self.db.add(tax)

        # Intentar hacer commit y manejar posibles errores
        try:
            self.db.commit()
            return {"status": "success", "message": "Tax saved successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
