from app.backend.db.models import BranchOfficeModel, SupervisorModel

class BranchOfficeClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, rol_id = None, rut = None, branch_office_id = None):
        try:
            if rol_id == 1 or rol_id == 2:
                data = self.db.query(BranchOfficeModel). \
                    filter(BranchOfficeModel.status_id == 7). \
                    order_by(BranchOfficeModel.branch_office). \
                    all()
            elif rol_id == 3:
                data = self.db.query(BranchOfficeModel). \
                    filter(BranchOfficeModel.status_id == 7). \
                    filter(BranchOfficeModel.principal_supervisor == rut). \
                    order_by(BranchOfficeModel.branch_office). \
                    all()
            else:
                data = self.db.query(BranchOfficeModel). \
                    filter(BranchOfficeModel.status_id == 7). \
                    filter(BranchOfficeModel.id == branch_office_id). \
                    order_by(BranchOfficeModel.branch_office). \
                    all()
            
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(BranchOfficeModel).filter(getattr(BranchOfficeModel, field) == value).filter(BranchOfficeModel.status_id == 7).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, branchOffice_inputs):
        try:
            data = BranchOfficeModel(**branchOffice_inputs)
            self.db.add(data)
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
        
    def update(self, id, branch_office):
        existing_branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == id).one_or_none()

        if not existing_branch_office:
            return "No data found"

        existing_branch_office_data = branch_office.dict(exclude_unset=True)
        for key, value in existing_branch_office_data.items():
            setattr(existing_branch_office, key, value)

        self.db.commit()

        return 1