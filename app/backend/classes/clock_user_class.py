from app.backend.db.models import ClockUserModel
from app.backend.classes.helper_class import HelperClass
from datetime import datetime

class ClockUserClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(ClockUserModel).order_by(ClockUserModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, clock_user_inputs):
        rut = HelperClass().numeric_rut(str(clock_user_inputs['rut']))

        status_id = self.verifiy(rut)

        last_uid = self.get_last_uid()

        if status_id == 0:
            clock_user = ClockUserModel()
            clock_user.uid = last_uid
            
            clock_user.rut = rut
            upper_string = clock_user_inputs['names'] + " " + clock_user_inputs['father_lastname']
            upper_string = HelperClass().upper_string(upper_string)
            clock_user.full_name = upper_string
            clock_user.privilege = clock_user_inputs['privilege']
            clock_user.added_date = datetime.now()
            clock_user.updated_date = datetime.now()

            self.db.add(clock_user)
            
            try:
                self.db.commit()

                return str(last_uid) + "_" + str(clock_user_inputs['rut']) + "_" + upper_string + "_" + str(clock_user_inputs['privilege'])
            except Exception as e:
                return 0
        else:
            upper_string = clock_user_inputs['names'] + " " + clock_user_inputs['father_lastname'] + " " + clock_user_inputs['mother_lastname']
            upper_string = HelperClass().upper_string(upper_string)

            return str(last_uid) + "_" + str(clock_user_inputs['rut']) + "_" + upper_string + "_" + str(clock_user_inputs['privilege'])
        
    
    def verifiy(self, rut = ''):
        clock_user_qty = self.db.query(ClockUserModel).filter(ClockUserModel.rut==rut).count()

        if clock_user_qty > 0:
            return 1
        else:
            return 0
        
    def get(self, field, value):
        try:
            data = self.db.query(ClockUserModel).filter(getattr(ClockUserModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get_last_uid(self):
        clock_user = self.db.query(ClockUserModel).filter(ClockUserModel.rut != '15538007').order_by(ClockUserModel.uid.desc()).first()
        result = clock_user.uid + 1

        return result
    
    def update(self, id, clock_user_inputs):
        if 'rut' in clock_user_inputs and clock_user_inputs['rut'] is not None:
            rut = HelperClass().numeric_rut(str(clock_user_inputs['rut']))

        status_id = self.verifiy(rut)

        if status_id == 0:
            clock_user =self.db.query(ClockUserModel).filter(ClockUserModel.rut == id).first()
            
            clock_user.rut = rut

            if 'names' in clock_user_inputs and clock_user_inputs['names'] is not None:
                upper_string = clock_user_inputs['names'] + " " + clock_user_inputs['father_lastname']
                upper_string = HelperClass().upper_string(upper_string)
                clock_user.full_name = upper_string
            
            if 'privilege' in clock_user_inputs and clock_user_inputs['privilege'] is not None:
                clock_user.privilege = clock_user_inputs['privilege']

            clock_user.updated_date = datetime.now()

            self.db.add(clock_user)
            
            try:
                self.db.commit()

                return 1
            except Exception as e:
                return 0