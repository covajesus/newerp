from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Pention, UpdatePention, UserLogin
from app.backend.classes.pention_class import PentionClass
from app.backend.auth.auth_user import get_current_active_user

pentions = APIRouter(
    prefix="/pentions",
    tags=["Pentions"]
)

@pentions.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PentionClass(db).get_all()

    return {"message": data}

@pentions.post("/store")
def store(pention:Pention, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    pention_inputs = pention.dict()
    data = PentionClass(db).store(pention_inputs)

    return {"message": data}

@pentions.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PentionClass(db).get("id", id)

    return {"message": data}

@pentions.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PentionClass(db).delete(id)

    return {"message": data}

@pentions.patch("/update/{id}")
def update(id: int, pention: UpdatePention, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PentionClass(db).update(id, pention)

    return {"message": data}