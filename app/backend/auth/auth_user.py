from typing import Optional

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from fastapi import HTTPException, Depends
from app.backend.db.models import UserModel, EmployeeModel, EmployeeLaborDatumModel, JobPositionModel
import os
from jose import jwt, JWTError
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
import bcrypt

oauth2_scheme = OAuth2PasswordBearer("/login_users/token")
oauth2_scheme_optional = OAuth2PasswordBearer("/login_users/token", auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        decoded_token = jwt.decode(token, os.environ['SECRET_KEY'], algorithms=[os.environ['ALGORITHM']])
        username = decoded_token.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})

    user = get_user(username)

    if user is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    return user
    
def get_current_active_user(current_user: UserModel = Depends(get_current_user)):
    return current_user


def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme_optional),
) -> Optional[UserModel]:
    """
    Usuario autenticado si el Bearer es válido; None si no hay token o es inválido.
    Sirve para endpoints que deben funcionar en público (p. ej. responder encuesta) y
    reforzar reglas cuando sí hay sesión.
    """
    if token is None or (isinstance(token, str) and not token.strip()):
        return None
    try:
        decoded_token = jwt.decode(
            token, os.environ["SECRET_KEY"], algorithms=[os.environ["ALGORITHM"]]
        )
        username = decoded_token.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    return get_user(username)


def get_user(rut):
    db: Session = next(get_db())

    user = db.query(UserModel). \
                    filter(UserModel.rut == rut). \
                    first()
    
    if not user:
        return None
    return user

def generate_bcrypt_hash(input_string):
    encoded_string = input_string.encode('utf-8')

    salt = bcrypt.gensalt()

    hashed_string = bcrypt.hashpw(encoded_string, salt)

    # Return as string, not bytes, for passlib compatibility
    return hashed_string.decode('utf-8')