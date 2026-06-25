from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.backend.auth.auth_user import get_current_active_user
from app.backend.classes.cashier_dte_class import CashierDteClass
from app.backend.db.database import get_db, get_db2
from app.backend.schemas import CashierDteSearch, UserLogin

cashier_dtes = APIRouter(
    prefix="/cashier_dtes",
    tags=["CashierDtes"],
)


@cashier_dtes.post("/search")
def search_cashier_dtes(
    body: CashierDteSearch,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    db2: Session = Depends(get_db2),
):
    del session_user  # auth required
    data = CashierDteClass(db2, db).search(
        branch_office_id=body.branch_office_id,
        amount=body.amount,
        since=body.since,
        until=body.until,
        page=body.page,
    )
    if isinstance(data, dict) and data.get("status") == "error":
        raise HTTPException(status_code=500, detail=data.get("message"))
    return {"message": data}


@cashier_dtes.get("/download/{dte_id}")
def download_cashier_dte_pdf(
    dte_id: int,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    db2: Session = Depends(get_db2),
):
    del session_user
    result = CashierDteClass(db2, db).download_pdf(dte_id)
    if isinstance(result, dict) and result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return {"message": result}
