from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import JobPosition, UpdateJobPosition, UserLogin
from app.backend.classes.job_position_class import JobPositionClass
from app.backend.auth.auth_user import get_current_active_user

job_positions = APIRouter(
    prefix="/job_positions",
    tags=["Job_Positions"]
)

@job_positions.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = JobPositionClass(db).get_all()

    return {"message": data}

@job_positions.post("/store")
def store(JobPosition:JobPosition, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    JobPosition_inputs = JobPosition.dict()
    data = JobPositionClass(db).store(JobPosition_inputs)

    return {"message": data}

@job_positions.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = JobPositionClass(db).get("id", id)

    return {"message": data}

@job_positions.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = JobPositionClass(db).delete(id)

    return {"message": data}

@job_positions.patch("/update/{id}")
def update(id: int, JobPosition: UpdateJobPosition, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = JobPositionClass(db).update(id, JobPosition)

    return {"message": data}