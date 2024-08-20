from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Region, UpdateRegion, UserLogin
from app.backend.classes.region_class import RegionClass
from app.backend.auth.auth_user import get_current_active_user

regions = APIRouter(
    prefix="/regions",
    tags=["Regions"]
)

@regions.get("/")
def index(db: Session = Depends(get_db)):
    data = RegionClass(db).get_all()

    return {"message": data}

@regions.post("/store")
def store(region:Region, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    region_inputs = region.dict()
    data = RegionClass(db).store(region_inputs)

    return {"message": data}

@regions.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = RegionClass(db).get("id", id)

    return {"message": data}

@regions.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = RegionClass(db).delete(id)

    return {"message": data}

@regions.patch("/update/{id}")
def update(id: int, region: UpdateRegion, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = RegionClass(db).update(id, region)

    return {"message": data}