from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import CivilState, UpdateCivilState, UserLogin
from app.backend.classes.civil_state_class import CivilStateClass
from app.backend.auth.auth_user import get_current_active_user

civil_states = APIRouter(
    prefix="/civil_states",
    tags=["Civil_States"]
)

@civil_states.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CivilStateClass(db).get_all()

    return {"message": data}

@civil_states.post("/store")
def store(civil_state:CivilState, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    civil_state_inputs = civil_state.dict()
    data = CivilStateClass(db).store(civil_state_inputs)

    return {"message": data}

@civil_states.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CivilStateClass(db).get("id", id)

    return {"message": data}

@civil_states.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CivilStateClass(db).delete(id)

    return {"message": data}

@civil_states.patch("/update/{id}")
def update(id: int, civil_state: UpdateCivilState, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CivilStateClass(db).update(id, civil_state)

    return {"message": data}