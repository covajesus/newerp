from datetime import datetime
from sqlalchemy.orm import Session
from app.backend.db.models import BranchOfficeModel, DepositModel
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import aliased
import json
from sqlalchemy import case
from app.backend.db.models import DepositModel, BranchOfficeModel
from sqlalchemy import func
from app.backend.classes.whatsapp_class import WhatsappClass

class DepositClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, rol_id=None, rut=None, branch_office_id=None, since=None, until=None, status_id=None, page=0, items_per_page=10):
        try:
            if rol_id == 1 or rol_id == 2:
                # Inicialización de filtros dinámicos
                filters = []
                if branch_office_id is not None:
                    filters.append(DepositModel.branch_office_id == branch_office_id)
                if status_id is not None:
                    filters.append(DepositModel.status_id == status_id)
                if since is not None:
                    filters.append(DepositModel.added_date >= since)
                if until is not None:
                    filters.append(DepositModel.added_date <= until)

                # Definir la prioridad de orden para status_id
                status_order = case(
                    (DepositModel.status_id == 1, 1),
                    (DepositModel.status_id == 3, 2),
                    (DepositModel.status_id == 6, 3),
                    else_=4  # Otros valores de status_id van al final
                )

                # Construir la consulta base con los filtros aplicados
                query = self.db.query(
                    DepositModel.id, 
                    DepositModel.branch_office_id, 
                    DepositModel.payment_type_id, 
                    DepositModel.collection_id,
                    DepositModel.status_id,
                    DepositModel.deposited_amount,   
                    DepositModel.payment_number, 
                    DepositModel.collection_amount,
                    func.date_format(DepositModel.collection_date, '%d-%m-%Y').label('collection_date'),
                    BranchOfficeModel.branch_office
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == DepositModel.branch_office_id
                ).filter(
                    *filters
                ).order_by(
                    status_order,  # Primero ordenamos por prioridad de status_id
                    DepositModel.collection_date.desc()  # Luego, ordenamos por ID dentro de cada grupo
                )
            else:
                # Inicialización de filtros dinámicos
                filters = []
                if branch_office_id is not None:
                    filters.append(DepositModel.branch_office_id == branch_office_id)
                if status_id is not None:
                    filters.append(DepositModel.status_id == status_id)
                if since is not None:
                    filters.append(DepositModel.added_date >= since)
                if until is not None:
                    filters.append(DepositModel.added_date <= until)

                # Definir la prioridad de orden para status_id
                status_order = case(
                    (DepositModel.status_id == 1, 1),
                    (DepositModel.status_id == 3, 2),
                    (DepositModel.status_id == 6, 3),
                    else_=4  # Otros valores de status_id van al final
                )

                # Construir la consulta base con los filtros aplicados
                query = self.db.query(
                    DepositModel.id, 
                    DepositModel.branch_office_id, 
                    DepositModel.payment_type_id, 
                    DepositModel.collection_id,
                    DepositModel.status_id,
                    DepositModel.deposited_amount,   
                    DepositModel.payment_number, 
                    DepositModel.collection_amount,
                    func.date_format(DepositModel.collection_date, '%d-%m-%Y').label('collection_date'),
                    BranchOfficeModel.branch_office
                ).outerjoin(
                    BranchOfficeModel, BranchOfficeModel.id == DepositModel.branch_office_id
                ).filter(
                    BranchOfficeModel.principal_supervisor == rut
                ).filter(
                    *filters
                ).order_by(
                    status_order,  # Primero ordenamos por prioridad de status_id
                    DepositModel.collection_date.desc()  # Luego, ordenamos por ID dentro de cada grupo
                )
                
            # Si se solicita paginación
            if page > 0:
                total_items = query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

            else:
                data = query.all()

            # Serializar los datos
            serialized_data = [{
                "id": deposit.id,
                "branch_office_id": deposit.branch_office_id,
                "payment_type_id": deposit.payment_type_id,
                "collection_id": deposit.collection_id,
                "status_id": deposit.status_id,
                "deposited_amount": deposit.deposited_amount,
                "payment_number": deposit.payment_number,
                "collection_amount": deposit.collection_amount,
                "collection_date": deposit.collection_date,
                "branch_office": deposit.branch_office
            } for deposit in data]

            if page > 0:
                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }
            else:
                return serialized_data

        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    def get(self, id):
        try:
            data_query = self.db.query(
                        DepositModel.id, 
                        DepositModel.branch_office_id, 
                        DepositModel.payment_type_id, 
                        DepositModel.collection_id,
                        DepositModel.status_id,
                        DepositModel.deposited_amount,   
                        DepositModel.payment_number, 
                        DepositModel.collection_amount,
                        DepositModel.collection_date, 
                        BranchOfficeModel.branch_office,
                        DepositModel.added_date,
                        DepositModel.support,
                        DepositModel.reject_reason_id
                        ). \
                        outerjoin(BranchOfficeModel, BranchOfficeModel.id == DepositModel.branch_office_id). \
                        filter(DepositModel.id == id). \
                        first()

            if data_query:
                # Serializar los datos del empleado
                patent_data = {
                    "id": data_query.id,
                    "branch_office_id": data_query.branch_office_id,
                    "payment_type_id": data_query.payment_type_id,
                    "collection_id": data_query.collection_id,
                    "status_id": data_query.status_id,
                    "deposited_amount": data_query.deposited_amount,
                    "payment_number": data_query.payment_number,
                    "collection_amount": data_query.collection_amount,
                    "collection_date": data_query.collection_date.strftime('%d-%m-%Y'),
                    "branch_office": data_query.branch_office,
                    "added_date": data_query.added_date.strftime('%d-%m-%Y'),
                    "support": data_query.support,
                    "reject_reason_id": data_query.reject_reason_id
                }

                # Crear el resultado final como un diccionario
                result = {
                    "deposit_data": patent_data
                }

                # Convierte el resultado a una cadena JSON
                serialized_result = json.dumps(result)

                return serialized_result

            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def store(self, form_data, support):
        # Crear una nueva instancia de DepositModel
        deposit = DepositModel()
        
        # Asignar los valores del formulario a la instancia del modelo
        deposit.branch_office_id = form_data.branch_office_id
        deposit.payment_type_id = form_data.payment_type_id
        deposit.collection_id = form_data.collection_id
        deposit.status_id = 1
        deposit.deposited_amount = form_data.deposited_amount
        deposit.payment_number = form_data.payment_number
        deposit.collection_amount = form_data.collection_amount
        deposit.collection_date = form_data.collection_date
        deposit.deposit_date = form_data.deposit_date
        deposit.support = support
        deposit.added_date = datetime.now()

        # Añadir la nueva instancia a la base de datos
        self.db.add(deposit)

        # Intentar hacer commit y manejar posibles errores
        try:
            self.db.commit()
            return {"status": "success", "message": "Deposit saved successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def _convert_date_format(self, date_str):
        """
        Convierte fecha de formato DD-MM-YYYY a YYYY-MM-DD para MySQL
        """
        if not date_str:
            return date_str
        
        try:
            # Si la fecha ya está en formato YYYY-MM-DD, devolverla tal como está
            if '-' in date_str and len(date_str.split('-')[0]) == 4:
                return date_str
            
            # Convertir de DD-MM-YYYY a YYYY-MM-DD
            date_obj = datetime.strptime(date_str, '%d-%m-%Y')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            # Si no se puede convertir, devolver la fecha original
            return date_str

    def accept(self, id, deposit_data=None):
        """
        Acepta un depósito y opcionalmente actualiza sus datos.
        Si encuentra un registro duplicado, lo actualiza en lugar de crear uno nuevo.
        
        Args:
            id: ID del depósito a aceptar
            deposit_data: Datos adicionales del depósito (objeto Deposit)
        """
        deposit = self.db.query(DepositModel).filter(DepositModel.id == id).first()
        if not deposit:
            raise HTTPException(status_code=404, detail="Depósito no encontrado")

        try:
            # Si se proporcionan datos adicionales, verificar si existe un duplicado
            if deposit_data:
                # Convertir fechas al formato correcto antes de la consulta
                deposit_date_formatted = self._convert_date_format(deposit_data.deposit_date)
                collection_date_formatted = self._convert_date_format(deposit_data.collection_date)
                
                # Verificar duplicados usando los mismos criterios que en store()
                existing_deposit = self.db.query(DepositModel).filter(
                    DepositModel.branch_office_id == deposit_data.branch_office_id,
                    DepositModel.payment_number == deposit_data.payment_number,
                    DepositModel.deposited_amount == deposit_data.deposited_amount,
                    DepositModel.deposit_date == deposit_date_formatted,
                    DepositModel.id != id  # Excluir el registro actual
                ).first()
                
                if existing_deposit:
                    # Si existe un duplicado, actualizar ese registro en lugar del actual
                    target_deposit = existing_deposit
                    # También marcar el depósito original como procesado si es diferente
                    if deposit.id != existing_deposit.id:
                        deposit.status_id = 6  # Aceptar el original también
                else:
                    # No hay duplicados, usar el depósito original
                    target_deposit = deposit
            else:
                # Sin datos adicionales, usar el depósito original
                target_deposit = deposit

            # Actualizar campos básicos
            target_deposit.status_id = 6

            # Si se proporcionan datos adicionales, actualizar los campos correspondientes
            if deposit_data:
                target_deposit.branch_office_id = deposit_data.branch_office_id
                target_deposit.payment_type_id = deposit_data.payment_type_id
                target_deposit.deposited_amount = deposit_data.deposited_amount
                target_deposit.deposit_date = deposit_date_formatted
                target_deposit.payment_number = deposit_data.payment_number
                target_deposit.collection_id = deposit_data.collection_id
                target_deposit.collection_amount = deposit_data.collection_amount
                target_deposit.collection_date = collection_date_formatted

            self.db.commit()
            self.db.refresh(target_deposit)
            
            message = "Depósito aceptado exitosamente"
            if deposit_data and existing_deposit and deposit.id != existing_deposit.id:
                message += " (se actualizó registro duplicado existente)"
            
            return {"status": "success", "message": message}
            
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error al aceptar depósito: {str(e)}"}

    def reject(self, id, deposit_data=None):
        """
        Rechaza un depósito y opcionalmente actualiza sus datos.
        Si encuentra un registro duplicado, lo actualiza en lugar de crear uno nuevo.
        
        Args:
            id: ID del depósito a rechazar
            deposit_data: Datos adicionales del depósito (objeto Deposit)
        """
        deposit = self.db.query(DepositModel).filter(DepositModel.id == id).first()
        if not deposit:
            raise HTTPException(status_code=404, detail="Depósito no encontrado")

        try:
            # Si se proporcionan datos adicionales, verificar si existe un duplicado
            if deposit_data:
                # Convertir fechas al formato correcto antes de la consulta
                deposit_date_formatted = self._convert_date_format(deposit_data.deposit_date)
                collection_date_formatted = self._convert_date_format(deposit_data.collection_date)
                
                # Verificar duplicados usando los mismos criterios que en store()
                existing_deposit = self.db.query(DepositModel).filter(
                    DepositModel.branch_office_id == deposit_data.branch_office_id,
                    DepositModel.payment_number == deposit_data.payment_number,
                    DepositModel.deposited_amount == deposit_data.deposited_amount,
                    DepositModel.deposit_date == deposit_date_formatted,
                    DepositModel.id != id  # Excluir el registro actual
                ).first()
                
                if existing_deposit:
                    # Si existe un duplicado, actualizar ese registro en lugar del actual
                    target_deposit = existing_deposit
                    # También marcar el depósito original como rechazado si es diferente
                    if deposit.id != existing_deposit.id:
                        deposit.status_id = 3  # Rechazar el original también
                else:
                    # No hay duplicados, usar el depósito original
                    target_deposit = deposit
            else:
                # Sin datos adicionales, usar el depósito original
                target_deposit = deposit

            # Actualizar campos básicos (status_id = 3 para rechazado)
            target_deposit.status_id = 3

            # Si se proporcionan datos adicionales, actualizar los campos correspondientes
            if deposit_data:
                target_deposit.branch_office_id = deposit_data.branch_office_id
                target_deposit.payment_type_id = deposit_data.payment_type_id
                target_deposit.deposited_amount = deposit_data.deposited_amount
                target_deposit.deposit_date = deposit_date_formatted
                target_deposit.payment_number = deposit_data.payment_number
                target_deposit.collection_id = deposit_data.collection_id
                target_deposit.collection_amount = deposit_data.collection_amount
                target_deposit.collection_date = collection_date_formatted
                # Agregar el reject_reason_id si está presente
                if hasattr(deposit_data, 'reject_reason_id') and deposit_data.reject_reason_id is not None:
                    target_deposit.reject_reason_id = deposit_data.reject_reason_id

            self.db.commit()
            self.db.refresh(target_deposit)
            
            # Enviar notificación WhatsApp
            try:
                whatsapp = WhatsappClass(self.db)
                whatsapp.rejected_deposit_notification(deposit_data, id)
            except Exception as whatsapp_error:
                print(f"Error al enviar WhatsApp: {str(whatsapp_error)}")
                # No fallar la operación principal por error de WhatsApp
            
            message = "Depósito rechazado exitosamente"
            if deposit_data and existing_deposit and deposit.id != existing_deposit.id:
                message += " (se actualizó registro duplicado existente)"
            
            return {"status": "success", "message": message}
            
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error al rechazar depósito: {str(e)}"}

    def update(self, id, form_data, support_file = None):
        """
        Actualiza los datos de la patente en la base de datos.
        """
        patent = self.db.query(PatentModel).filter(PatentModel.id == id).first()
        if not patent:
            raise HTTPException(status_code=404, detail="Patente no encontrada")

        # Actualizar campos
        patent.branch_office_id = form_data.branch_office_id
        patent.semester = form_data.semester
        patent.year = form_data.year
        if support_file != None:
            patent.support = support_file

        self.db.commit()
        self.db.refresh(patent)

    def delete(self, id):
        try:
            self.db.query(DepositModel).filter(DepositModel.id == id).delete()
            self.db.commit()

            return {"status": "success", "message": "Deposit deleted successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        