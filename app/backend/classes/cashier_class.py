from app.backend.db.models import CashierModel, LatestUpdateCashierModel, BranchOfficeModel
import json
from datetime import datetime
import pytz

class CashierClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, branch_office_id = ''):
        try:
            if branch_office_id == '':
                data = self.db.query(CashierModel).filter(CashierModel.folio_segment_id != 9).order_by(CashierModel.cashier).all()
            else :
                data = self.db.query(CashierModel).filter(CashierModel.branch_office_id == branch_office_id).filter(CashierModel.folio_segment_id != 9).order_by(CashierModel.cashier).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(CashierModel).filter(getattr(CashierModel, field) == value).order_by(CashierModel.cashier).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def get_subscriber_cashier(self, branch_office_id):
        try:
            data = self.db.query(CashierModel).filter(CashierModel.branch_office_id == branch_office_id).filter(CashierModel.folio_segment_id == 9).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
         
    def get_with_machine(self, id):
        try:
            data = self.db.query(CashierModel).filter(CashierModel.getaway_machine_id == 1). filter(CashierModel.branch_office_id == id).first()
            
            return data.id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def latest_update(self):
        cashier_reports = self.db.query(LatestUpdateCashierModel).all()

        if not cashier_reports:
            return "No hay cajas en el informe."
        
        serialized_data = []
        for cashier_report in cashier_reports:
            cashier_report_dict = {
                "id": cashier_report.id,
                "cashier": cashier_report.cashier,
                "last_updated_date": cashier_report.last_updated_date.isoformat() if cashier_report.last_updated_date else None,
                "rustdesk": cashier_report.rustdesk,
                "anydesk": cashier_report.anydesk
            }
            serialized_data.append(cashier_report_dict)

        return json.dumps(serialized_data)
    
    def get_list(self, page=0, items_per_page=10):
        try:
            # Inicialización de filtros dinámicos
            filters = []

            # Construir la consulta base con los filtros aplicados
            query = self.db.query(
                CashierModel.id,
                CashierModel.cashier,
                CashierModel.branch_office_id,
                CashierModel.folio_segment_id,
                CashierModel.getaway_machine_id,
                CashierModel.added_date,
                CashierModel.updated_date,
                CashierModel.anydesk,
                CashierModel.rustdesk,
                CashierModel.available_folios,
                BranchOfficeModel.branch_office
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == CashierModel.branch_office_id
            ).filter(
                CashierModel.folio_segment_id != 9,
                CashierModel.folio_segment_id != 8,
                CashierModel.folio_segment_id != 0
            ).filter(
                *filters
            ).order_by(
                CashierModel.id
            )

            if page > 0:
                total_items = query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                serialized_data = [{
                    "id": cashier.id,
                    "cashier": cashier.cashier,
                    "branch_office_id": cashier.branch_office_id,
                    "folio_segment_id": cashier.folio_segment_id,
                    "getaway_machine_id": cashier.getaway_machine_id,
                    "added_date": cashier.added_date.isoformat() if cashier.added_date else None,
                    "updated_date": cashier.updated_date.isoformat() if cashier.updated_date else None,
                    "anydesk": cashier.anydesk,
                    "rustdesk": cashier.rustdesk,
                    "available_folios": cashier.available_folios,
                    "branch_office": cashier.branch_office
                } for cashier in data]

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }

            else:
                data = query.all()

                serialized_data = [{
                    "id": cashier.id,
                    "cashier": cashier.cashier,
                    "branch_office_id": cashier.branch_office_id,
                    "folio_segment_id": cashier.folio_segment_id,
                    "getaway_machine_id": cashier.getaway_machine_id,
                    "added_date": cashier.added_date.isoformat() if cashier.added_date else None,
                    "updated_date": cashier.updated_date.isoformat() if cashier.updated_date else None,
                    "anydesk": cashier.anydesk,
                    "rustdesk": cashier.rustdesk,
                    "available_folios": cashier.available_folios,
                    "branch_office": cashier.branch_office
                } for cashier in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
    
    def update_all_cashiers(self, cashiers_data: list):
        tz = pytz.timezone('America/Santiago')
        current_date = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

        for data in cashiers_data:
            cashier_id = data[0]
            available_folios = data[1]

            record = self.db.query(CashierModel).filter_by(
                id=cashier_id
            ).first()

            if record:
                if record.available_folios != available_folios:
                    record.available_folios = available_folios
                    record.updated_date = current_date

                    self.db.commit()
            else:
                new_data = {
                    'cashier_id': cashier_id,
                    'available_folios': available_folios,
                    'updated_date': current_date
                }
                new_record = CashierModel(**new_data)
                self.db.add(new_record)

                self.db.commit()

    def get_all_cashiers(self):
        data = (
            self.db.query(
                CashierModel.id,
                CashierModel.available_folios
            )
            .filter(CashierModel.folio_segment_id != 9)
            .filter(CashierModel.folio_segment_id != 8)
            .all()
        )
        return data

        return data
        
    def search(self, cashier_inputs, page=0, items_per_page=10):
        try:
            # Inicialización de filtros dinámicos
            filters = []
            if cashier_inputs.branch_office_id is not None and cashier_inputs.branch_office_id != '':
                filters.append(CashierModel.branch_office_id == cashier_inputs.branch_office_id)
            if cashier_inputs.cashier_id is not None and cashier_inputs.cashier_id != '':
                filters.append(CashierModel.id == cashier_inputs.cashier_id)
           
            # Construir la consulta base con los filtros aplicados
            query = self.db.query(
                CashierModel.id,
                CashierModel.cashier,
                CashierModel.branch_office_id,
                CashierModel.folio_segment_id,
                CashierModel.getaway_machine_id,
                CashierModel.added_date,
                CashierModel.updated_date,
                CashierModel.anydesk,
                CashierModel.rustdesk,
                CashierModel.available_folios,
                BranchOfficeModel.branch_office
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == CashierModel.branch_office_id
            ).filter(
                CashierModel.folio_segment_id != 9,
                CashierModel.folio_segment_id != 8,
                CashierModel.folio_segment_id != 0
            ).filter(
                *filters
            ).order_by(
                CashierModel.id
            )

            print(str(query.statement))


            if page > 0:
                total_items = query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                serialized_data = [{
                    "id": cashier.id,
                    "cashier": cashier.cashier,
                    "branch_office_id": cashier.branch_office_id,
                    "folio_segment_id": cashier.folio_segment_id,
                    "getaway_machine_id": cashier.getaway_machine_id,
                    "added_date": cashier.added_date.isoformat() if cashier.added_date else None,
                    "updated_date": cashier.updated_date.isoformat() if cashier.updated_date else None,
                    "anydesk": cashier.anydesk,
                    "rustdesk": cashier.rustdesk,
                    "available_folios": cashier.available_folios,
                    "branch_office": cashier.branch_office
                } for cashier in data]

                return {
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": serialized_data
                }

            else:
                data = query.all()

                serialized_data = [{
                    "id": cashier.id,
                    "cashier": cashier.cashier,
                    "branch_office_id": cashier.branch_office_id,
                    "folio_segment_id": cashier.folio_segment_id,
                    "getaway_machine_id": cashier.getaway_machine_id,
                    "added_date": cashier.added_date.isoformat() if cashier.added_date else None,
                    "updated_date": cashier.updated_date.isoformat() if cashier.updated_date else None,
                    "anydesk": cashier.anydesk,
                    "rustdesk": cashier.rustdesk,
                    "available_folios": cashier.available_folios,
                    "branch_office": cashier.branch_office
                } for cashier in data]

                return serialized_data

        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}
        
    def store(self, form_data):
        cashier = CashierModel()
        cashier.cashier = form_data.cashier
        cashier.branch_office_id = form_data.branch_office_id
        cashier.getaway_machine_id = form_data.getaway_machine_id
        cashier.transbank_status_id = form_data.transbank_status_id
        cashier.visibility_status_id = form_data.visibility_status_id
        cashier.folio_segment_id = form_data.folio_segment_id
        cashier.anydesk = form_data.anydesk
        cashier.rustdesk = form_data.rustdesk

        self.db.add(cashier)

        try:
            self.db.commit()
            return {"status": "success", "message": "Cashier saved successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}
        
    def update(self, id, form_data):
        cashier = self.db.query(CashierModel).filter(CashierModel.id == id).one_or_none()

        if not cashier:
            return {"status": "error", "message": "Cashier not found"}

        # Solo actualizar si el campo está en form_data y no es None
        for field in [
            "cashier",
            "branch_office_id",
            "getaway_machine_id",
            "transbank_status_id",
            "visibility_status_id",
            "folio_segment_id",
            "anydesk",
            "rustdesk"
        ]:
            value = getattr(form_data, field, None)
            if value is not None:
                setattr(cashier, field, value)

        try:
            self.db.commit()
            return {"status": "success", "message": "Cashier updated successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error: {str(e)}"}

    def delete(self, id):
        try:
            data = self.db.query(CashierModel).filter(CashierModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"