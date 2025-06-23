from app.backend.db.models import BranchOfficeModel, RegionModel, ZoneModel

class BranchOfficeClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, rol_id = None, rut = None, branch_office_id = None):
        try:
            if rol_id == 1 or rol_id == 2 or rol_id == 3:
                data = self.db.query(BranchOfficeModel). \
                    filter(BranchOfficeModel.status_id == 7). \
                    filter(BranchOfficeModel.visibility_id == 1). \
                    order_by(BranchOfficeModel.branch_office). \
                    all()
            elif rol_id == 4:
                data = self.db.query(BranchOfficeModel). \
                    filter(BranchOfficeModel.status_id == 7). \
                    filter(BranchOfficeModel.visibility_id == 1). \
                    filter(BranchOfficeModel.principal_supervisor == rut). \
                    order_by(BranchOfficeModel.branch_office). \
                    all()
            elif rol_id == 5:
                data = self.db.query(BranchOfficeModel). \
                    filter(BranchOfficeModel.status_id == 7). \
                    filter(BranchOfficeModel.visibility_id == 1). \
                    order_by(BranchOfficeModel.branch_office). \
                    all()
            elif rol_id == 6:
                data = self.db.query(BranchOfficeModel). \
                    filter(BranchOfficeModel.status_id == 7). \
                    filter(BranchOfficeModel.visibility_id == 1). \
                    filter(BranchOfficeModel.id == branch_office_id). \
                    order_by(BranchOfficeModel.branch_office). \
                    all()

            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get_all_basement(self, rol_id = None, rut = None, branch_office_id = None):
        try:
            if rol_id == 1 or rol_id == 2 or rol_id == 3:
                data = self.db.query(BranchOfficeModel). \
                    filter(BranchOfficeModel.status_id == 7). \
                    filter(BranchOfficeModel.visibility_id == 1). \
                    filter(BranchOfficeModel.basement_id == 1). \
                    order_by(BranchOfficeModel.branch_office). \
                    all()
            elif rol_id == 4:
                data = self.db.query(BranchOfficeModel). \
                    filter(BranchOfficeModel.status_id == 7). \
                    filter(BranchOfficeModel.visibility_id == 1). \
                    filter(BranchOfficeModel.basement_id == 1). \
                    filter(BranchOfficeModel.principal_supervisor == rut). \
                    order_by(BranchOfficeModel.branch_office). \
                    all()
            elif rol_id == 5:
                data = self.db.query(BranchOfficeModel). \
                    filter(BranchOfficeModel.status_id == 7). \
                    filter(BranchOfficeModel.visibility_id == 1). \
                    filter(BranchOfficeModel.basement_id == 1). \
                    order_by(BranchOfficeModel.branch_office). \
                    all()
            elif rol_id == 6:
                data = self.db.query(BranchOfficeModel). \
                    filter(BranchOfficeModel.status_id == 7). \
                    filter(BranchOfficeModel.basement_id == 1). \
                    filter(BranchOfficeModel.visibility_id == 1). \
                    filter(BranchOfficeModel.id == branch_office_id). \
                    order_by(BranchOfficeModel.branch_office). \
                    all()
            
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get_full_data(self):
        try:
            data = self.db.query(BranchOfficeModel). \
                    order_by(BranchOfficeModel.branch_office). \
                    all()
            
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def get_with_machine(self):
        try:
            data = self.db.query(BranchOfficeModel). \
                    filter(BranchOfficeModel.getaway_machine_id == 1). \
                    order_by(BranchOfficeModel.branch_office). \
                    all()
            
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get(self, field, value):
        try:
            data = self.db.query(BranchOfficeModel).filter(getattr(BranchOfficeModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, branch_office_inputs):
        try:
            branch_office = BranchOfficeModel()
            branch_office.branch_office = branch_office_inputs.branch_office
            branch_office.dte_code = branch_office_inputs.dte_code
            branch_office.address = branch_office_inputs.address
            branch_office.region_id = branch_office_inputs.region_id
            branch_office.commune_id = branch_office_inputs.commune_id
            branch_office.segment_id = branch_office_inputs.segment_id
            branch_office.zone_id = branch_office_inputs.zone_id
            branch_office.principal_id = branch_office_inputs.principal_id
            branch_office.principal_supervisor = branch_office_inputs.principal_supervisor
            branch_office.getaway_machine_id = branch_office_inputs.getaway_machine_id
            branch_office.basement_id = branch_office_inputs.basement_id
            branch_office.status_id = branch_office_inputs.status_id
            branch_office.visibility_id = branch_office_inputs.visibility_id
            branch_office.opening_date = branch_office_inputs.opening_date
            
            self.db.add(branch_office)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, form_data):
        try:
            existing_branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == form_data.id).one_or_none()

            if not existing_branch_office:
                return "No data found"
            
            existing_branch_office.branch_office = form_data.branch_office
            existing_branch_office.address = form_data.address
            existing_branch_office.dte_code = form_data.dte_code
            existing_branch_office.region_id = form_data.region_id
            existing_branch_office.commune_id = form_data.commune_id
            existing_branch_office.segment_id = form_data.segment_id
            existing_branch_office.zone_id = form_data.zone_id
            existing_branch_office.principal_id = form_data.principal_id
            existing_branch_office.principal_supervisor = form_data.principal_supervisor
            existing_branch_office.getaway_machine_id = form_data.getaway_machine_id
            existing_branch_office.basement_id = form_data.basement_id
            existing_branch_office.status_id = form_data.status_id
            existing_branch_office.visibility_id = form_data.visibility_id
            existing_branch_office.opening_date = form_data.opening_date

            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"