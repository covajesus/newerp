from app.backend.db.models import ScheduleModel
import json
from sqlalchemy import or_, asc
from collections import defaultdict


class ScheduleClass:
    def __init__(self, db):
        self.db = db
    def store(self, data):
        try:
            # Get the last week_schedule_id in the database
            last_schedule = self.db.query(ScheduleModel).order_by(ScheduleModel.id.desc()).first()
            
            if last_schedule is None:
                new_week_schedule_id = 1
            else:
                if last_schedule.week_schedule_id is None:
                    new_week_schedule_id = 1
                else:
                    new_week_schedule_id = last_schedule.week_schedule_id + 1

            for day, day_data in data.schedule.items():
                if isinstance(day_data, str) and day_data == "No hay turno para este día":
                    schedule = {}
                else:
                    schedule = ScheduleModel(
                        day=day, 
                        turn_id=day_data.id if day_data.id is not None else 0, 
                        week_schedule_id=new_week_schedule_id, 
                        start=day_data.start if day_data.start is not None else 0, 
                        end=day_data.end if day_data.end is not None else 0, 
                        horary_name=data.horary_name if data.horary_name is not None else 0
                    )
                    self.db.add(schedule)
            self.db.commit()
            return "Data stored"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def get_all(self):
        try:
            data = (self.db.query(ScheduleModel)
                    .order_by(asc(ScheduleModel.week_schedule_id))
                    .all())

            grouped_data = defaultdict(list)
            for item in data:
                grouped_data[item.week_schedule_id].append(item)

            return list(grouped_data.values())
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def get(self, employee_type_id, group_id, search_term=None):
        try:
            query = self.db.query(ScheduleModel).\
                filter(ScheduleModel.employee_type_id == employee_type_id, ScheduleModel.group_id == group_id)
            
            if search_term and search_term != "Buscar Turno":
                # Asume que `turn` es el campo que quieres buscar
                query = query.filter(or_(ScheduleModel.turn.contains(search_term)))
            
            data = query.all()
            
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"