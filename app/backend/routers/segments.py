from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Segment, UpdateSegment, UserLogin
from app.backend.classes.segment_class import SegmentClass
from app.backend.auth.auth_user import get_current_active_user

segments = APIRouter(
    prefix="/segments",
    tags=["Segments"]
)

@segments.get("/")
def index(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = SegmentClass(db).get_all()

    return {"message": data}

@segments.post("/store")
def store(segment:Segment, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    segment_inputs = segment.dict()
    data = SegmentClass(db).store(segment_inputs)

    return {"message": data}

@segments.get("/edit/{id}")
def edit(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = SegmentClass(db).get("id", id)

    return {"message": data}

@segments.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = SegmentClass(db).delete(id)

    return {"message": data}

@segments.patch("/update/{id}")
def update(id: int, Segment: UpdateSegment, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = SegmentClass(db).update(id, Segment)

    return {"message": data}