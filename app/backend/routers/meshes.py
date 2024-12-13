from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Mesh,  UserLogin, MeshList
from app.backend.classes.mesh_class import MeshClass
from app.backend.classes.helper_class import HelperClass
from app.backend.auth.auth_user import get_current_active_user


meshes = APIRouter(
    prefix="/meshes",
    tags=["Mesh"]
)

@meshes.get("/")
def get_all(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = MeshClass(db).get_all()

    return {"message": data}

@meshes.post("/store")
def store(mesh_list: MeshList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):

    mesh_inputs_array = []
    for mesh in mesh_list.meshes:
        mesh_inputs = mesh.dict()
        mesh_inputs_array.append(mesh_inputs)
    data = MeshClass(db).store(mesh_inputs_array)
    # print(data)
    return {"message": "Data stored successfully", "data": data}

@meshes.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = MeshClass(db).get("id", id)

    return {"message": data}

@meshes.get("/last_week_working_days/{rut}/{date}")
def last_week_working_days(rut:int, date:str , session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    dateSplit = HelperClass().split(str(date),'-' )
    data = MeshClass(db).last_week_working_days(rut, dateSplit[0], dateSplit[1])
    data = MeshClass(db).quantity_last_week_working_days(rut, dateSplit[0], dateSplit[1], data)

    return {"message": data}

@meshes.get("/get_mesh_by_rut_week_period/{rut}/{period}")
def getMeshByrutWeekPeriod(rut:int, period:str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = MeshClass(db).getMeshByrutWeekPeriod(rut, period)

    return {"message": data}

@meshes.get("/get_all_meshes_by_supervisor/{supervisor_rut}")
def get_all_by_supervisor(supervisor_rut: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = MeshClass(db).get_all_meshes_by_supervisor(supervisor_rut)

    return {"message": data}

@meshes.get("/get_all_employees_by_supervisor/{supervisor_rut}")
def get_all_employees_by_supervisor(supervisor_rut: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = MeshClass(db).get_all_employees_by_supervisor(supervisor_rut)

    return {"message": data}

@meshes.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = MeshClass(db).deleteMesh(id)

    return {"message": data}