from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import FamilyType, UpdateFamilyType
from app.backend.classes.family_type_class import FamilyTypeClass

family_types = APIRouter(
    prefix="/family_types",
    tags=["Family_Types"]
)

@family_types.get("/")
def index(db: Session = Depends(get_db)):
    data = FamilyTypeClass(db).get_all()

    return {"message": data}

@family_types.post("/store")
def store(family_type:FamilyType, db: Session = Depends(get_db)):
    family_type_inputs = family_type.dict()
    data = FamilyTypeClass(db).store(family_type_inputs)

    return {"message": data}

@family_types.get("/edit/{id}")
def edit(id:int, db: Session = Depends(get_db)):
    data = FamilyTypeClass(db).get("id", id)

    return {"message": data}

@family_types.delete("/delete/{id}")
def delete(id:int, db: Session = Depends(get_db)):
    data = FamilyTypeClass(db).delete(id)

    return {"message": data}

@family_types.patch("/update/{id}")
def update(id: int, family_type: UpdateFamilyType, db: Session = Depends(get_db)):
    data = FamilyTypeClass(db).update(id, family_type)

    return {"message": data}