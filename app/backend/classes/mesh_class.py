from app.backend.db.models import MeshModel, EmployeeModel, MeshDetailModel, TurnModel, EmployeeLaborDatumModel
from sqlalchemy import desc, asc,extract, select
import json
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from calendar import monthrange


class MeshClass:
    def __init__(self, db):
        self.db = db

    # Función para serializar los datos de un objeto MeshModel
    def serialize_mesh(self, mesh):
        return {
            'turn': mesh.turn,
            'working': mesh.working,
            'start': str(mesh.start), 
            'end': str(mesh.end),
            'breaking': mesh.breaking,
            'group_day_id': mesh.group_day_id,
            'free_day_group_id': mesh.free_day_group_id,
            'total_week_hours': mesh.total_week_hours,
            'scheduled': f'{mesh.group_day_id} x {mesh.free_day_group_id}',
        }
    # Función para obtener los datos de un turno por su id
    def get_turn_by_id(self, id):
        stmt = select(TurnModel.turn, TurnModel.working, TurnModel.start, TurnModel.end, TurnModel.breaking, TurnModel.group_day_id, TurnModel.free_day_group_id, TurnModel.total_week_hours).where(TurnModel.id == id)
        result = self.db.execute(stmt).first()
        return self.serialize_mesh(result)
        
    # Función para agrupar los datos por semana
    def group_by_week(self, data):
        grouped_data = {}
        for item in data:
            week_id = item['week_id']
            if week_id not in grouped_data:
                # Si la semana no está en el diccionario, la agregamos
                turn_data = self.get_turn_by_id(item['turn_id'])
                grouped_data[week_id] = {
                    'week_id': week_id,
                    'turn_id': item['turn_id'],
                    'mesh_id': item['mesh_id'],
                    'rut': item['rut'],
                    'added_date': item['added_date'],
                    'turn_data': turn_data,
                    'date': [{
                        'date': item['date'],
                        'is_sunday': item['is_sunday'],
                        'is_working': item['is_working']
                    }]
                }
            else:
                # Si la semana ya está en el diccionario, agregamos la fecha a la lista
                grouped_data[week_id]['date'].append({
                    'date': item['date'],
                    'is_sunday': item['is_sunday'],
                    'is_working': item['is_working']
                })
        return list(grouped_data.values())

    # Función para obtener los datos de un turno por rut, semana y periodo, ejemplo rut = 12345678-9, week = 1, period = 2021-01    
    def getMeshByrutWeekPeriod(self, rut, period):
        try:
            periodYear = period.split('-')[0]
            periodMonth = period.split('-')[1]
            data = self.db.query(MeshDetailModel).filter(MeshDetailModel.rut == rut)\
                        .filter(extract('year', MeshDetailModel.date) == periodYear)\
                        .filter(extract('month', MeshDetailModel.date) == periodMonth).all()
            data = [item.__dict__ for item in data]  # Convertir los objetos a diccionarios
            grouped_data = self.group_by_week(data)
            return grouped_data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
   
    def get_all(self):
        try:
            data = self.db.query(MeshModel, EmployeeModel).outerjoin(EmployeeModel, MeshModel.rut == EmployeeModel.rut).order_by(desc(MeshModel.id)).all()
            return [row._asdict() for row in data]
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    # función para obtener todas las mallas horarias por supervisor
    def get_all_meshes_by_supervisor(self, supervisor_rut):
        try:
           
            supervisor = (self.db.query(EmployeeLaborDatumModel)
                          .filter(EmployeeLaborDatumModel.rut == supervisor_rut)
                          .first())
            if supervisor is None:
                return f"Error: No supervisor found with rut {supervisor_rut}"

            supervisor_branch_office_id = supervisor.branch_office_id

            # Obtener todos los empleados que tienen el mismo branch_office_id
            data = (self.db.query(MeshModel, EmployeeModel, EmployeeLaborDatumModel)
                    .outerjoin(EmployeeModel, MeshModel.rut == EmployeeModel.rut)
                    .outerjoin(EmployeeLaborDatumModel, EmployeeModel.rut == EmployeeLaborDatumModel.rut)
                    .filter(EmployeeLaborDatumModel.branch_office_id == supervisor_branch_office_id)
                    .order_by(desc(MeshModel.id))
                    .all())
            
            return [row._asdict() for row in data]
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    # Función para obtener todos los empleados por supervisor
    def get_all_employees_by_supervisor(self, supervisor_rut):
        try:
            # Obtener el branch_office_id del supervisor
            supervisor = (self.db.query(EmployeeLaborDatumModel)
                          .filter(EmployeeLaborDatumModel.rut == supervisor_rut)
                          .first())
            if supervisor is None:
                return f"Error: No supervisor found with rut {supervisor_rut}"

            supervisor_branch_office_id = supervisor.branch_office_id

            # Obtener todos los empleados que tienen el mismo branch_office_id
            data = (self.db.query(EmployeeModel, EmployeeLaborDatumModel)
                    .outerjoin(EmployeeLaborDatumModel, EmployeeModel.rut == EmployeeLaborDatumModel.rut)
                    .filter(EmployeeLaborDatumModel.branch_office_id == supervisor_branch_office_id)
                    .all())
            
            return [{**{column.name: getattr(row.EmployeeModel, column.name) for column in EmployeeModel.__table__.columns},
                     **{column.name: getattr(row.EmployeeLaborDatumModel, column.name) for column in EmployeeLaborDatumModel.__table__.columns}} for row in data]
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    # Función para calcular la cantidad de días trabajados en la ultima semana del mes pasado, para luego la primera semana del mes que sigue se resten los días trabajados del turno seleccionado
    def quantity_last_week_working_days(self, rut, year, month, dataLastWeek):
                data_dict = json.loads(dataLastWeek)
                try:
                    data = self.db.query(MeshDetailModel)\
                        .filter(MeshDetailModel.rut == rut)\
                        .filter(extract('year', MeshDetailModel.date) == year)\
                        .filter(extract('month', MeshDetailModel.date) == month)\
                        .filter(MeshDetailModel.week_id == data_dict['week_id'] )\
                        .filter(MeshDetailModel.is_working == 1)\
                        .count()      
                    return data
                except Exception as e:
                    error_message = str(e)
                    return f"Error: {error_message}"
    
    # Función para obtener los datos de la ultima semana del mes pasado
    def last_week_working_days(self, rut, year, month):
        try:
            data = self.db.query(MeshDetailModel)\
                .filter(MeshDetailModel.rut == rut)\
                .filter(extract('year', MeshDetailModel.date) == year)\
                .filter(extract('month', MeshDetailModel.date) == month)\
                .order_by(desc(MeshDetailModel.week_id))\
                .first()      
            
            if data:
                # Serializar el objeto MeshModel a un diccionario
                mesh_data = {
                    'id': data.id,
                    'turn_id': data.turn_id,
                    'week_id': data.week_id,
                    'rut': data.rut,
                    'date': data.date.strftime("%Y-%m-%d"),
                    'added_date': data.added_date.strftime("%Y-%m-%d"),  # Convert the datetime object to a string format
                }

                # Convierte el diccionario a una cadena JSON
                serialized_data = json.dumps(mesh_data)

                return serialized_data
            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def get(self, field, value):
        try:
            data = self.db.query(MeshModel).filter(getattr(MeshModel, field) == value).first()

            if data:
                # Serializar el objeto MeshModel a un diccionario
                mesh_data = {
                    'id': data.id,
                    'turn_id': data.turn_id,
                    'week_id': data.week_id,
                    'rut': data.rut,
                    'added_date': data.added_date.strftime("%Y-%m-%d"), 
                }


                # Convierte el diccionario a una cadena JSON
                serialized_data = json.dumps(mesh_data)

                return serialized_data

            else:
                return "No se encontraron datos para el campo especificado."

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
  
    
    def validate(self, mesh_data):
        mesh_data = self.db.query(MeshModel).filter_by(rut=mesh_data['rut'], period=mesh_data['period']).first()
        return mesh_data
    
    def validate_mesh_detail(self, mesh_id, date):
        mesh_detail = self.db.query(MeshDetailModel).filter_by(mesh_id=mesh_id, date=date).count()
        return mesh_detail

    def store(self, inputs):
        try:
            first_date = datetime.fromisoformat(inputs[0]['date'])
            period = f"{first_date.year}-{first_date.month}"
            mesh_data = {key: inputs[0][key] for key in ('rut', 'added_date')}
            mesh_data['period'] = period

            validation = self.validate(mesh_data)
            if not validation:
                mesh = MeshModel(**mesh_data)
                self.db.add(mesh)
                self.db.commit()

            _, num_days = monthrange(first_date.year, first_date.month)
            all_days = [datetime(first_date.year, first_date.month, day) for day in range(1, num_days+1)]
            
            input_dates = [datetime.fromisoformat(input['date']).date() for input in inputs]
    
            week_id = 1
           
            # Preprocesar los datos de entrada para obtener los datos de la semana siguiente
            next_week_data = {}
            for inp in inputs:
                week_of_year = datetime.fromisoformat(inp['date']).date().isocalendar()[1]
                next_week_data[week_of_year] = inp

            # Variables para almacenar los datos de la semana actual
            current_turn_id = None
            current_rut = None
            current_added_date = None

            for day in all_days:
                formatted_date = day.strftime('%Y-%m-%d %H:%M:%S')
                week_of_year = day.date().isocalendar()[1]

                # Si hay datos para la semana siguiente, actualizar los datos actuales
                if week_of_year in next_week_data:
                    current_turn_id = next_week_data[week_of_year]['turn_id']
                    current_rut = next_week_data[week_of_year]['rut']
                    current_added_date = next_week_data[week_of_year]['added_date']

                is_working = False
                for inp in inputs:
                    if day.date() == datetime.fromisoformat(inp['date']).date():
                        is_working = True
                        break

                detail_data = {
                    'week_id': week_id,
                    'turn_id': current_turn_id,
                    'mesh_id': mesh.id,
                    'rut': current_rut,
                    'date': formatted_date,
                    'added_date': current_added_date,
                    'is_working': is_working,
                    'is_sunday': day.weekday() == 6,
                }

                detail = MeshDetailModel(**detail_data)

                self.db.add(detail)
                self.db.commit()

                if day.weekday() == 6:  # Si el día es domingo
                    week_id += 1  # Incrementa week_id
                        
        
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def deleteMesh(self, id):
        try:
           
            mesh_details = self.db.query(MeshDetailModel).filter(MeshDetailModel.mesh_id == id).all()
            for detail in mesh_details:
                self.db.delete(detail)

         
            mesh = self.db.query(MeshModel).filter(MeshModel.id == id).first()
            if mesh:
                self.db.delete(mesh)
                self.db.commit()
                return 1
            else:
                return 0 
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
