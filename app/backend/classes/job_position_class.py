from app.backend.db.models import JobPositionModel

class JobPositionClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(JobPositionModel).order_by(JobPositionModel.job_position).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(JobPositionModel).filter(getattr(JobPositionModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, jobPosition_inputs):
        try:
            data = JobPositionModel(**jobPosition_inputs)
            self.db.add(data)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(JobPositionModel).filter(JobPositionModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, jobPosition):
        existing_job_position = self.db.query(JobPositionModel).filter(JobPositionModel.id == id).one_or_none()
        print(jobPosition)
        if not existing_job_position:
            return "No data found"

        existing_job_position_type_data = jobPosition.dict(exclude_unset=True)
        for key, value in existing_job_position_type_data.items():
            setattr(existing_job_position, key, value)

        self.db.commit()

        return 1