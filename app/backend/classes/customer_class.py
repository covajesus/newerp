from app.backend.db.models import CustomerModel, RegionModel, CommuneModel
import json
from sqlalchemy.dialects import mysql
from datetime import datetime
from fastapi import HTTPException

class CustomerClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, rut = None, page = 1, items_per_page = 10):
        try:
            # Inicialización de filtros dinámicos
            filters = []
            if rut is not None:
                filters.append(CustomerModel.rut == rut)

            # Construir la consulta base con los filtros aplicados
            query = self.db.query(
                CustomerModel.id, 
                CustomerModel.rut, 
                CustomerModel.customer, 
                CustomerModel.region_id, 
                CustomerModel.commune_id,
                CustomerModel.email,
                CustomerModel.phone,
                CustomerModel.activity,
                CustomerModel.address
            ).filter(
                *filters
            ).order_by(
                CustomerModel.rut
            )

            # Si se solicita paginación
            if page > 0:
                # Calcular el total de registros
                total_items = query.count()
                print(query.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))

                total_pages = (total_items + items_per_page - 1) // items_per_page
                print(total_pages)
                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                # Aplicar paginación en la consulta
                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                # Serializar los datos
                serialized_data = [{
                    "id": customer.id,
                    "rut": customer.rut,
                    "customer": customer.customer,
                    "region_id": customer.region_id,
                    "commune_id": customer.commune_id,
                    "customer": customer.email,
                    "phone": customer.phone,
                    "customer": customer.activity,
                    "address": customer.address
                } for customer in data]

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }

            # Si no se solicita paginación, traer todos los datos
            else:
                data = query.all()

                # Serializar los datos
                serialized_data = [{
                    "id": customer.id,
                    "rut": customer.rut,
                    "customer": customer.customer,
                    "region_id": customer.region_id,
                    "commune_id": customer.commune_id,
                    "customer": customer.email,
                    "phone": customer.phone,
                    "customer": customer.activity,
                    "address": customer.address
                } for customer in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}

    def get_by_rut(self, rut):
        try:
            data_query = self.db.query(CustomerModel.rut, RegionModel.region, CommuneModel.commune, CustomerModel.customer, CustomerModel.phone, CustomerModel.email, CustomerModel.region_id, CustomerModel.commune_id, CustomerModel.activity, CustomerModel.address). \
                        outerjoin(RegionModel, RegionModel.id == CustomerModel.region_id). \
                        outerjoin(CommuneModel, CommuneModel.id == CustomerModel.commune_id). \
                        filter(CustomerModel.rut == rut). \
                        first()

            if data_query:
                # Serializar los datos del empleado
                customer_data = {
                    "rut": data_query.rut,
                    "customer": data_query.customer,
                    "region_id": data_query.region_id,
                    "region": data_query.region,
                    "commune": data_query.commune,
                    "commune_id": data_query.commune_id,
                    "phone": data_query.phone,
                    "email": data_query.email,
                    "activity": data_query.activity,
                    "address": data_query.address
                }

                result = {
                    "customer_data": customer_data
                }

                # Convierte el resultado a una cadena JSON
                serialized_result = json.dumps(result)

                return serialized_result
            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    

    def get(self, id):
        try:
            data_query = self.db.query(CustomerModel.rut, CustomerModel.customer, CustomerModel.phone, CustomerModel.email, CustomerModel.region_id, CustomerModel.commune_id, CustomerModel.activity, CustomerModel.address). \
                        filter(CustomerModel.id == id). \
                        first()

            if data_query:
                # Serializar los datos del empleado
                customer_data = {
                    "rut": data_query.rut,
                    "customer": data_query.customer,
                    "region_id": data_query.region_id,
                    "commune_id": data_query.commune_id,
                    "phone": data_query.phone,
                    "email": data_query.email,
                    "activity": data_query.activity,
                    "address": data_query.address
                }

                result = {
                    "customer_data": customer_data
                }

                # Convierte el resultado a una cadena JSON
                serialized_result = json.dumps(result)

                return serialized_result
            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def check_existence(self, rut):
        try:
            data_query = self.db.query(CustomerModel.rut, RegionModel.region, CommuneModel.commune, CustomerModel.customer, CustomerModel.phone, CustomerModel.email, CustomerModel.region_id, CustomerModel.commune_id, CustomerModel.activity, CustomerModel.address). \
                        outerjoin(RegionModel, RegionModel.id == CustomerModel.region_id). \
                        outerjoin(CommuneModel, CommuneModel.id == CustomerModel.commune_id). \
                        filter(CustomerModel.rut == rut). \
                        first()

            if data_query:
                # Serializar los datos del empleado
                customer_data = {
                    "rut": data_query.rut,
                    "customer": data_query.customer,
                    "region_id": data_query.region_id,
                    "commune_id": data_query.commune_id,
                    "phone": data_query.phone,
                    "email": data_query.email,
                    "activity": data_query.activity,
                    "address": data_query.address,
                    "region": data_query.region,
                    "commune": data_query.commune
                }

                result = {
                    "customer_data": customer_data
                }

                # Convierte el resultado a una cadena JSON
                serialized_result = json.dumps(result)

                return serialized_result
            else:
                return "Customer does not exist"

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def store(self, form_data):
                # Crear una nueva instancia de ContractModel
        customer = CustomerModel()
        
        # Asignar los valores del formulario a la instancia del modelo
        customer.rut = form_data.rut
        customer.region_id = form_data.region_id
        customer.commune_id = form_data.commune_id
        customer.customer = form_data.customer.upper()
        customer.email = form_data.email
        customer.activity = form_data.activity.upper()
        customer.phone = form_data.phone
        customer.address = form_data.address.upper()
        customer.added_date = datetime.now()

        # Añadir la nueva instancia a la base de datos
        self.db.add(customer)

        # Intentar hacer commit y manejar posibles errores
        try:
            self.db.commit()
            return {"status": "success", "message": "Customer saved successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def delete(self, id):
        try:
            data = self.db.query(CustomerModel).filter(CustomerModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return f"success"
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, rut, form_data):
        """
        Actualiza los datos de la patente en la base de datos.
        """
        print(id)
        customer = self.db.query(CustomerModel).filter(CustomerModel.rut == rut).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        customer.region_id = form_data.region_id
        customer.commune_id = form_data.commune_id
        customer.customer = form_data.customer.upper()
        customer.email = form_data.email
        customer.activity = form_data.activity.upper()
        customer.phone = form_data.phone
        customer.address = form_data.address.upper()

        self.db.commit()
        self.db.refresh(customer)