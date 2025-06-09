from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.group_detail_class import GroupDetailClass
from app.backend.schemas import GroupDetail, StoreGroupDetail, UpdateGroupDetail

group_details = APIRouter(
    prefix="/group_details",
    tags=["GroupDetails"]
)

@group_details.post("/")
def index(group_detail_inputs: GroupDetail, db: Session = Depends(get_db)):
    data = GroupDetailClass(db).get_all(group_detail_inputs.page)

    return {"message": data}

@group_details.get("/list")
def list(db: Session = Depends(get_db)):
    data = GroupDetailClass(db).get_list()

    return {"message": data}

@group_details.post("/store")
def store(group_detail_inputs: StoreGroupDetail, db: Session = Depends(get_db)):
    data = GroupDetailClass(db).store(group_detail_inputs)
    return {"message": data}

@group_details.delete("/delete/{id}")
def delete(id: int, db: Session = Depends(get_db)):
    GroupDetailClass(db).delete(id)

    return {"message": "success"}

@group_details.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    data = GroupDetailClass(db).get(id)

    return {"message": data}

@group_details.post("/update")
def post(update_group_detail: UpdateGroupDetail, db: Session = Depends(get_db)):
    data = GroupDetailClass(db).update(update_group_detail)

    return {"message": data}
