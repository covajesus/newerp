from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from app.backend.classes.authentication_class import AuthenticationClass
from sqlalchemy.orm import Session

authentications = APIRouter(
    prefix="/authentications",
    tags=["Authentications"]
)

@authentications.get("/get_token")
def get_token(db: Session = Depends(get_db)):
    print(2222)
    authentication_class = AuthenticationClass(db).get_token()

    return {"message": authentication_class}

