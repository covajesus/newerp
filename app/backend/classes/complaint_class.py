from app.backend.db.models import ComplaintModel
from datetime import datetime

class ComplaintClass:
    def __init__(self, db):
        self.db = db
    
    def store(self, complaint_inputs):
        complaint = ComplaintModel()
        complaint.relationship = complaint_inputs['relationship']
        complaint.incident_place = complaint_inputs['incident_place']
        complaint.complaint_type = complaint_inputs['complaint_type']
        complaint.anonymous = complaint_inputs['anonymous']
        complaint.incident_date = complaint_inputs['incident_date']
        complaint.incident_place_detail = complaint_inputs['incident_place_detail']
        complaint.knowledge = complaint_inputs['knowledge']
        complaint.identify = complaint_inputs['identify']
        complaint.description = complaint_inputs['description']
        complaint.support = ''
        complaint.password = complaint_inputs['password']
        complaint.email = complaint_inputs['email']
        complaint.status = 0
        complaint.added_date = datetime.now()

        self.db.add(complaint)

        try:
            self.db.commit()

            return complaint.id
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    
    def update(self, id, support):
        complaint =  self.db.query(ComplaintModel).filter(ComplaintModel.id == id).one_or_none()
        
        complaint.support = support

        self.db.add(complaint)

        try:
            self.db.commit()

            return 1
        except Exception as e:
            return 0
        

    def verify(self, data):
        complaint =  self.db.query(ComplaintModel).filter(ComplaintModel.id == data['id']).filter(ComplaintModel.password == data['password']).count()

        if complaint > 0:
            complaint =  self.db.query(ComplaintModel).filter(ComplaintModel.id == data['id']).one_or_none()

            return complaint.status
        else:
            return None
    