from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin, GetBudget
from app.backend.classes.budget_class import BudgetClass
from app.backend.auth.auth_user import get_current_active_user

budgets = APIRouter(
    prefix="/budgets",
    tags=["Budgets"]
)

@budgets.post("/total")
def total(user: GetBudget, session_user: UserLogin = Depends(get_current_active_user)):
    user_inputs = user.dict()
    data = BudgetClass.get_total(user_inputs)

    return {"message": data}