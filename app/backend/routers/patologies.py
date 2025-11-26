from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Pention, UpdatePention
from app.backend.classes.pention_class import PentionClass

pentions = APIRouter(
    prefix="/pentions",
    tags=["Pentions"]
)

@pentions.get("/")
def index(db: Session = Depends(get_db)):
    data = PentionClass(db).get_all()

    return {"message": data}

@pentions.post("/store")
def store(pention:Pention, db: Session = Depends(get_db)):
    pention_inputs = pention.dict()
    data = PentionClass(db).store(pention_inputs)

    return {"message": data}

@pentions.get("/edit/{id}")
def edit(id:int, db: Session = Depends(get_db)):
    data = PentionClass(db).get("id", id)

    return {"message": data}

@pentions.delete("/delete/{id}")
def delete(id:int, db: Session = Depends(get_db)):
    data = PentionClass(db).delete(id)

    return {"message": data}

@pentions.patch("/update/{id}")
def update(id: int, pention: UpdatePention, db: Session = Depends(get_db)):
    data = PentionClass(db).update(id, pention)

    return {"message": data}