from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.authentication_class import AuthenticationClass
from app.backend.classes.rol_class import RolClass
from datetime import timedelta
import json

authentications = APIRouter(
    prefix="/authentications",
    tags=["Authentications"]
)

@authentications.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = AuthenticationClass(db).authenticate_user(form_data.username, form_data.password)

    rol = RolClass(db).get('id', user["user_data"]["rol_id"])
    token_expires = timedelta(minutes=30)
    token = AuthenticationClass(db).create_token({'sub': str(user["user_data"]["rut"])}, token_expires)

    return {
        "access_token": token,
        "rut": user["user_data"]["rut"],
        "rol_id": user["user_data"]["rol_id"],
        "rol": rol.rol,
        "full_name": user["user_data"]["full_name"],
        "email": user["user_data"]["email"],
        "token_type": "bearer"
    }

@authentications.post("/logout")
def logout(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = AuthenticationClass(db).authenticate_user(form_data.username, form_data.password)
    access_token_expires = timedelta(minutes=30)
    access_token_jwt = AuthenticationClass(db).create_token({'sub': str(user.rut)}, access_token_expires)

    return {
        "access_token": access_token_jwt, 
        "rut": user.rut,
        "visual_rut": user.visual_rut,
        "rol_id": user.rol_id,
        "nickname": user.nickname,
        "token_type": "bearer"
    }