from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from app.backend.classes.setting_class import SettingClass
from sqlalchemy.orm import Session

settings = APIRouter(
    prefix="/settings",
    tags=["Settings"]
)

@settings.get("/get_token")
def get_token(db: Session = Depends(get_db)):
    setting_data = SettingClass(db).get()

    return {"message": setting_data}


