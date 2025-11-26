from app.backend.db.models import MedicalLicenseModel, DocumentEmployeeModel, EmployeeModel, PayrollItemValueModel, PayrollItemModel
from datetime import datetime
from sqlalchemy import desc, func
from app.backend.classes.dropbox_class import DropboxClass
import json

class SalarySettlementClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(MedicalLicenseModel).order_by(MedicalLicenseModel.id).all()
            if not data:
                return "No hay registros"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get_taxable_assets(self, rut, period):
        data = self.db.query(PayrollItemValueModel).join(PayrollItemModel, PayrollItemModel.id == PayrollItemValueModel.item_id).filter(PayrollItemModel.salary_settlement_location_id == 1).add_columns(
                PayrollItemValueModel.id,
                PayrollItemValueModel.item_id,
                PayrollItemValueModel.rut,
                PayrollItemValueModel.amount,
                PayrollItemValueModel.period,
                PayrollItemModel.salary_settlement_name,
                PayrollItemModel.item
            ).filter(PayrollItemValueModel.rut == rut, PayrollItemValueModel.period == period).all()


        result = []
        for item_value in data:
            result.append({
                "id": item_value.id,
                "item_id": item_value.item_id,
                "rut": item_value.rut,
                "amount": item_value.amount,
                "name": item_value.salary_settlement_name,
                "period": item_value.period,
                "item": item_value.item
            })

        return result
    
    def get_total_taxable_assets(self, rut, period):
        data = self.db.query(PayrollItemValueModel).join(PayrollItemModel, PayrollItemModel.id == PayrollItemValueModel.item_id).filter(PayrollItemModel.salary_settlement_location_id == 2).add_columns(
                PayrollItemValueModel.id,
                PayrollItemValueModel.item_id,
                PayrollItemValueModel.rut,
                PayrollItemValueModel.amount,
                PayrollItemValueModel.period,
                PayrollItemModel.salary_settlement_name,
                PayrollItemModel.item
            ).filter(PayrollItemValueModel.rut == rut, PayrollItemValueModel.period == period).all()


        result = []
        for item_value in data:
            result.append({
                "id": item_value.id,
                "item_id": item_value.item_id,
                "rut": item_value.rut,
                "amount": item_value.amount,
                "name": item_value.salary_settlement_name,
                "period": item_value.period,
                "item": item_value.item
            })

        return result

    def get_no_taxable_assets(self, rut, period):
        data = self.db.query(PayrollItemValueModel).join(PayrollItemModel, PayrollItemModel.id == PayrollItemValueModel.item_id).filter(PayrollItemModel.salary_settlement_location_id == 3).add_columns(
                PayrollItemValueModel.id,
                PayrollItemValueModel.item_id,
                PayrollItemValueModel.rut,
                PayrollItemValueModel.amount,
                PayrollItemValueModel.period,
                PayrollItemModel.salary_settlement_name,
                PayrollItemModel.item
            ).filter(PayrollItemValueModel.rut == rut, PayrollItemValueModel.period == period).all()


        result = []
        for item_value in data:
            result.append({
                "id": item_value.id,
                "item_id": item_value.item_id,
                "rut": item_value.rut,
                "amount": item_value.amount,
                "name": item_value.salary_settlement_name,
                "period": item_value.period,
                "item": item_value.item
            })

        return result
    
    def get_total_no_taxable_assets(self, rut, period):
        data = self.db.query(PayrollItemValueModel).join(PayrollItemModel, PayrollItemModel.id == PayrollItemValueModel.item_id).filter(PayrollItemModel.salary_settlement_location_id == 4).add_columns(
                PayrollItemValueModel.id,
                PayrollItemValueModel.item_id,
                PayrollItemValueModel.rut,
                PayrollItemValueModel.amount,
                PayrollItemValueModel.period,
                PayrollItemModel.salary_settlement_name,
                PayrollItemModel.item
            ).filter(PayrollItemValueModel.rut == rut, PayrollItemValueModel.period == period).all()


        result = []
        for item_value in data:
            result.append({
                "id": item_value.id,
                "item_id": item_value.item_id,
                "rut": item_value.rut,
                "amount": item_value.amount,
                "name": item_value.salary_settlement_name,
                "period": item_value.period,
                "item": item_value.item
            })

        return result
    
    def get_legal_discounts(self, rut, period):
        data = self.db.query(PayrollItemValueModel).join(PayrollItemModel, PayrollItemModel.id == PayrollItemValueModel.item_id).filter(PayrollItemModel.salary_settlement_location_id == 5).add_columns(
                PayrollItemValueModel.id,
                PayrollItemValueModel.item_id,
                PayrollItemValueModel.rut,
                PayrollItemValueModel.amount,
                PayrollItemValueModel.period,
                PayrollItemModel.salary_settlement_name,
                PayrollItemModel.item
            ).filter(PayrollItemValueModel.rut == rut, PayrollItemValueModel.period == period).all()


        result = []
        for item_value in data:
            result.append({
                "id": item_value.id,
                "item_id": item_value.item_id,
                "rut": item_value.rut,
                "amount": item_value.amount,
                "name": item_value.salary_settlement_name,
                "period": item_value.period,
                "item": item_value.item
            })

        return result
    
    def get_total_legal_discounts(self, rut, period):
        data = self.db.query(PayrollItemValueModel).join(PayrollItemModel, PayrollItemModel.id == PayrollItemValueModel.item_id).filter(PayrollItemModel.salary_settlement_location_id == 6).add_columns(
                PayrollItemValueModel.id,
                PayrollItemValueModel.item_id,
                PayrollItemValueModel.rut,
                PayrollItemValueModel.amount,
                PayrollItemValueModel.period,
                PayrollItemModel.salary_settlement_name,
                PayrollItemModel.item
            ).filter(PayrollItemValueModel.rut == rut, PayrollItemValueModel.period == period).all()


        result = []
        for item_value in data:
            result.append({
                "id": item_value.id,
                "item_id": item_value.item_id,
                "rut": item_value.rut,
                "amount": item_value.amount,
                "name": item_value.salary_settlement_name,
                "period": item_value.period,
                "item": item_value.item
            })

        return result

    def get_other_legal_discounts(self, rut, period):
        data = self.db.query(PayrollItemValueModel).join(PayrollItemModel, PayrollItemModel.id == PayrollItemValueModel.item_id).filter(PayrollItemModel.salary_settlement_location_id == 7).add_columns(
                PayrollItemValueModel.id,
                PayrollItemValueModel.item_id,
                PayrollItemValueModel.rut,
                PayrollItemValueModel.amount,
                PayrollItemModel.salary_settlement_name,
                PayrollItemValueModel.period,
                PayrollItemModel.item
            ).filter(PayrollItemValueModel.rut == rut, PayrollItemValueModel.period == period).all()


        result = []
        for item_value in data:
            result.append({
                "id": item_value.id,
                "item_id": item_value.item_id,
                "rut": item_value.rut,
                "amount": item_value.amount,
                "name": item_value.salary_settlement_name,
                "period": item_value.period,
                "item": item_value.item
            })

        return result
    
    def get_total_other_legal_discounts(self, rut, period):
        data = self.db.query(PayrollItemValueModel).join(PayrollItemModel, PayrollItemModel.id == PayrollItemValueModel.item_id).filter(PayrollItemModel.salary_settlement_location_id == 8).add_columns(
                PayrollItemValueModel.id,
                PayrollItemValueModel.item_id,
                PayrollItemValueModel.rut,
                PayrollItemValueModel.amount,
                PayrollItemModel.salary_settlement_name,
                PayrollItemValueModel.period,
                PayrollItemModel.item
            ).filter(PayrollItemValueModel.rut == rut, PayrollItemValueModel.period == period).all()


        result = []
        for item_value in data:
            result.append({
                "id": item_value.id,
                "item_id": item_value.item_id,
                "rut": item_value.rut,
                "amount": item_value.amount,
                "name": item_value.salary_settlement_name,
                "period": item_value.period,
                "item": item_value.item
            })

        return result
    
    def get_total_pay(self, rut, period):
        data = self.db.query(PayrollItemValueModel).join(PayrollItemModel, PayrollItemModel.id == PayrollItemValueModel.item_id).filter(PayrollItemModel.salary_settlement_location_id == 10).add_columns(
                PayrollItemValueModel.id,
                PayrollItemValueModel.item_id,
                PayrollItemValueModel.rut,
                PayrollItemValueModel.amount,
                PayrollItemModel.salary_settlement_name,
                PayrollItemValueModel.period,
                PayrollItemModel.item
            ).filter(PayrollItemValueModel.rut == rut, PayrollItemValueModel.period == period).all()


        result = []
        for item_value in data:
            result.append({
                "id": item_value.id,
                "item_id": item_value.item_id,
                "rut": item_value.rut,
                "amount": item_value.amount,
                "name": item_value.salary_settlement_name,
                "period": item_value.period,
                "item": item_value.item
            })

        return result
    
    def get_working_days(self, rut, period):
        data = self.db.query(PayrollItemValueModel).join(PayrollItemModel, PayrollItemModel.id == PayrollItemValueModel.item_id).filter(PayrollItemValueModel.item_id == 55).add_columns(
                PayrollItemValueModel.id,
                PayrollItemValueModel.item_id,
                PayrollItemValueModel.rut,
                PayrollItemValueModel.amount,
                PayrollItemValueModel.period,
                PayrollItemModel.item
            ).filter(PayrollItemValueModel.rut == rut, PayrollItemValueModel.period == period).all()

        result = []

        for item_value in data:
            result.append({
                "id": item_value.id,
                "item_id": item_value.item_id,
                "rut": item_value.rut,
                "amount": item_value.amount,
                "period": item_value.period,
                "item": item_value.item
            })

        return result

    # Obtiene todos los registros de licencias medicas con paginacion
    def get_new_all_with_pagination(self, page = 1, items_per_page = 10):
        try:

            data_query = self.db.query(
                        DocumentEmployeeModel.added_date,
                        DocumentEmployeeModel.period,
                        DocumentEmployeeModel.document_type_id,
                        DocumentEmployeeModel.support,
                        DocumentEmployeeModel.status_id,
                        DocumentEmployeeModel.old_document_status_id,
                        DocumentEmployeeModel.id,
                        EmployeeModel.names,
                        EmployeeModel.father_lastname,
                        EmployeeModel.mother_lastname,
                        EmployeeModel.visual_rut,
                        EmployeeModel.rut
                    ).outerjoin(EmployeeModel, EmployeeModel.rut == DocumentEmployeeModel.rut).filter(DocumentEmployeeModel.old_document_status_id == 0).filter(DocumentEmployeeModel.document_type_id == 5).order_by(desc(DocumentEmployeeModel.id))

            total_items = data_query.count()
            total_pages = (total_items + items_per_page - 1) // items_per_page

            if page < 1 or page > total_pages:
                return "Invalid page number"

            data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

            if not data:
                return "No data found"

            # Serializar los datos en una estructura de diccionario
            serialized_data = {
                        "total_items": total_items,
                        "total_pages": total_pages,
                        "current_page": page,
                        "items_per_page": items_per_page,
                        "data": [
                            {
                                "added_date": item.added_date.strftime('%Y-%m-%d %H:%M:%S') if item.added_date else None,
                                "document_type_id": item.document_type_id,
                                "old_document_status_id": item.old_document_status_id,
                                "support": item.support,
                                "status_id": item.status_id,
                                "id": item.id,
                                "period": item.period,
                                "names": item.names,
                                "visual_rut": item.visual_rut,
                                "father_lastname": item.father_lastname,
                                "mother_lastname": item.mother_lastname,
                                "rut": item.rut
                            }
                            for item in data
                        ]
                    }

            # Convierte el resultado a una cadena JSON
            serialized_result = json.dumps(serialized_data)

            return serialized_result
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
         
    # Obtiene todos los registros de licencias medicas con paginacion
    def get_all_with_pagination(self, page = 1, items_per_page = 10):
        try:

            data_query = self.db.query(
                        DocumentEmployeeModel.added_date,
                        DocumentEmployeeModel.period,
                        DocumentEmployeeModel.document_type_id,
                        DocumentEmployeeModel.support,
                        DocumentEmployeeModel.status_id,
                        DocumentEmployeeModel.old_document_status_id,
                        DocumentEmployeeModel.id,
                        EmployeeModel.names,
                        EmployeeModel.father_lastname,
                        EmployeeModel.mother_lastname,
                        EmployeeModel.visual_rut,
                        EmployeeModel.rut
                    ).outerjoin(EmployeeModel, EmployeeModel.rut == DocumentEmployeeModel.rut).filter(DocumentEmployeeModel.old_document_status_id != 0).filter(DocumentEmployeeModel.document_type_id == 5).order_by(desc(DocumentEmployeeModel.id))

            total_items = data_query.count()
            total_pages = (total_items + items_per_page - 1) // items_per_page

            if page < 1 or page > total_pages:
                return "Invalid page number"

            data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

            if not data:
                return "No data found"

            # Serializar los datos en una estructura de diccionario
            serialized_data = {
                        "total_items": total_items,
                        "total_pages": total_pages,
                        "current_page": page,
                        "items_per_page": items_per_page,
                        "data": [
                            {
                                "added_date": item.added_date.strftime('%Y-%m-%d %H:%M:%S') if item.added_date else None,
                                "document_type_id": item.document_type_id,
                                "old_document_status_id": item.old_document_status_id,
                                "support": item.support,
                                "status_id": item.status_id,
                                "id": item.id,
                                "period": item.period,
                                "names": item.names,
                                "visual_rut": item.visual_rut,
                                "father_lastname": item.father_lastname,
                                "mother_lastname": item.mother_lastname,
                                "rut": item.rut
                            }
                            for item in data
                        ]
                    }

            # Convierte el resultado a una cadena JSON
            serialized_result = json.dumps(serialized_data)

            return serialized_result
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    # Obtiene un registro de liquidacion de sueldo filtrados y paginados    
    def get(self, field, value, type = 1, page = 1, items_per_page = 10):
        try:
                if type == 1:
                    data = self.db.query(DocumentEmployeeModel).filter(getattr(DocumentEmployeeModel, field) == value).filter(DocumentEmployeeModel.document_type_id == 5).first()
                    if data:
                        return {
                            "added_date": data.added_date.strftime('%Y-%m-%d %H:%M:%S') if data.added_date else None,
                            "document_type_id": data.document_type_id,
                            "support": data.support,
                            "status_id": data.status_id,
                            "id": data.id
                        }
                    else:
                        return "No data found"
                else:
                    data_query = self.db.query(
                        DocumentEmployeeModel.added_date,
                        DocumentEmployeeModel.document_type_id,
                        DocumentEmployeeModel.support,
                        DocumentEmployeeModel.status_id,
                        DocumentEmployeeModel.id
                    ).outerjoin(EmployeeModel, EmployeeModel.rut == DocumentEmployeeModel.rut).filter(getattr(DocumentEmployeeModel, field) == value).filter(DocumentEmployeeModel.document_type_id == 5).order_by(desc(DocumentEmployeeModel.id))

                    total_items = data_query.count()
                    total_pages = (total_items + items_per_page - 1) // items_per_page

                    if page < 1 or page > total_pages:
                        return "Invalid page number"

                    data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                    if not data:
                        return "No data found"

                    # Serializar los datos en una estructura de diccionario
                    serialized_data = {
                        "total_items": total_items,
                        "total_pages": total_pages,
                        "current_page": page,
                        "items_per_page": items_per_page,
                        "data": [
                            {
                                "added_date": item.added_date.strftime('%Y-%m-%d %H:%M:%S') if item.added_date else None,
                                "document_type_id": item.document_type_id,
                                "support": item.support,
                                "status_id": item.status_id,
                                "id": item.id
                            }
                            for item in data
                        ]
                    }

                    # Convierte el resultado a una cadena JSON
                    serialized_result = json.dumps(serialized_data)

                    return serialized_result
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def download(self, id):
        try:
            data = self.db.query(DocumentEmployeeModel).filter(DocumentEmployeeModel.id == id).first()

            file = DropboxClass(self.db).get('/salary_settlements/', data.support)

            return file
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def store(self, salary_settlement_inputs, support):
        try:
            salary_settlement = DocumentEmployeeModel()
            salary_settlement.status_id = salary_settlement_inputs.status_id
            salary_settlement.rut = salary_settlement_inputs.rut
            salary_settlement.document_type_id = salary_settlement_inputs.document_type_id
            salary_settlement.support = support
            salary_settlement.added_date = datetime.now()
            salary_settlement.updated_date = datetime.now()

            self.db.add(salary_settlement)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def existence (self, rut, period):
        quantity = (
            self.db.query(DocumentEmployeeModel)
            .filter(
                DocumentEmployeeModel.rut == rut,
                func.date_format(DocumentEmployeeModel.added_date, '%Y-%m') == period
            )
            .filter(
                DocumentEmployeeModel.old_document_status_id == 0
            )
            .count()
        )

        return quantity

    def new_store(self, rut, period):
        existence_status = self.existence(rut, period)

        if existence_status == 0 or existence_status == None:
            try:
                salary_settlement = DocumentEmployeeModel()
                salary_settlement.status_id = 4
                salary_settlement.rut = rut
                salary_settlement.document_type_id = 5
                salary_settlement.old_document_status_id = 0
                salary_settlement.period = period
                salary_settlement.support = ''
                salary_settlement.added_date = datetime.now()
                salary_settlement.updated_date = datetime.now()

                self.db.add(salary_settlement)
                self.db.commit()
                return 1
            except Exception as e:
                error_message = str(e)
                return f"Error: {error_message}"
            
    def store_multiple(self, salary_settlement_inputs, support):
        try:
            salary_settlement = DocumentEmployeeModel()
            salary_settlement.status_id = 3
            salary_settlement.rut = salary_settlement_inputs['rut']
            salary_settlement.document_type_id = 5
            salary_settlement.support = support
            salary_settlement.added_date = datetime.now()
            salary_settlement.updated_date = datetime.now()

            self.db.add(salary_settlement)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete_salary_settlement(self, id):
        try:
            data = self.db.query(DocumentEmployeeModel).filter(DocumentEmployeeModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"