from app.backend.db.models import PossibleEmployeesModel
from datetime import datetime
from sqlalchemy import func



class PossibleEmployeeClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        possible = self.db.query(PossibleEmployeesModel).all()
        return possible
    
    def store(self, data, file):
        possible  = PossibleEmployeesModel()
        possible.rut = data.rut
        possible.names = data.names
        possible.father_lastname = data.father_lastname
        possible.mother_lastname = data.mother_lastname
        possible.cellphone = data.cellphone
        possible.picture = file
        possible.added_date = datetime.now()
        possible.updated_date = datetime.now()

        self.db.add(possible)
        self.db.commit()
        return 1
    

    