from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from app.backend.classes.setting_class import SettingClass
from app.backend.schemas import UpdateSetting
from sqlalchemy.orm import Session

settings = APIRouter(
    prefix="/settings",
    tags=["Settings"]
)

@settings.get("/get_token")
def get_token(db: Session = Depends(get_db)):
    setting_data = SettingClass(db).get()
    print(setting_data)

    # Devuelve el contenido directamente dentro de "message"
    return {"message": setting_data["setting_data"]}

@settings.get("/edit/{id}")
def edit(id:int, db: Session = Depends(get_db)):
    settings = SettingClass(db).get()

    return {"message": settings}

@settings.post("/update")
def update(form_data: UpdateSetting = Depends(UpdateSetting.as_form), db: Session = Depends(get_db)):
    SettingClass(db).update(form_data)
    return {"message": "Settings updated successfully"}

