from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin, SearchBranchOfficeTransbank, BranchOfficeTransbankList
from app.backend.classes.branch_office_transbank_class import BranchOfficeTransbankClass
from app.backend.auth.auth_user import get_current_active_user

branch_office_transbank = APIRouter(
    prefix="/branch_office_transbank",
    tags=["BranchOfficeTransbank"]
)

@branch_office_transbank.post("/")
def index(
    list_data: BranchOfficeTransbankList,
    session_user: UserLogin = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    data = BranchOfficeTransbankClass(db).get_all(
        page=list_data.page, 
        items_per_page=list_data.items_per_page,
        branch_office_id=list_data.branch_office_id
    )
    return {"message": data}