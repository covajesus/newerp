from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Any
from app.backend.db.database import get_db
from app.backend.classes.accounting_entry_class import AccountingEntryClass

accounting_entries = APIRouter(
    prefix="/accounting_entries",
    tags=["AccountingEntries"],
)

accounting_accounts = APIRouter(
    prefix="/accounting_accounts",
    tags=["AccountingAccounts"],
)


class AccountingEntryLineInput(BaseModel):
    account_code: str
    debit: int = 0
    credit: int = 0
    concept: Optional[str] = None


class AccountingEntryDocumentInput(BaseModel):
    doc_type: str = "emitido"
    issuer_rut: Optional[str] = None
    dte_type_id: Optional[int] = None
    folio: Optional[int] = None
    period: Optional[str] = None


class AccountingEntryCreate(BaseModel):
    glosa: str
    entry_date: str
    operation: Optional[str] = None
    annulled: int = 0
    lines: List[AccountingEntryLineInput] = []
    documents: List[AccountingEntryDocumentInput] = []
    user_id: Optional[int] = None


class AccountingEntrySearch(BaseModel):
    period: Optional[str] = None
    number: Optional[int] = None
    since: Optional[str] = None
    until: Optional[str] = None
    glosa: Optional[str] = None
    annulled: Optional[int] = None
    user_id: Optional[int] = None
    page: int = 1
    items_per_page: int = 20


class AccountingAccountCreate(BaseModel):
    code: str
    name: str


@accounting_entries.post("/search")
def search(payload: AccountingEntrySearch, db: Session = Depends(get_db)):
    data = AccountingEntryClass(db).search(
        period=payload.period,
        number=payload.number,
        since=payload.since,
        until=payload.until,
        glosa=payload.glosa,
        annulled=payload.annulled,
        user_id=payload.user_id,
        page=payload.page,
        items_per_page=payload.items_per_page,
    )
    return {"message": data}


@accounting_entries.get("/{entry_id}")
def get_entry(entry_id: int, db: Session = Depends(get_db)):
    data = AccountingEntryClass(db).get(entry_id)
    return {"message": data}


@accounting_entries.post("/")
def create_entry(payload: AccountingEntryCreate, db: Session = Depends(get_db)):
    data = AccountingEntryClass(db).store_manual(payload, user_id=payload.user_id)
    return {"message": data}


@accounting_entries.post("/{entry_id}/annul")
def annul_entry(entry_id: int, db: Session = Depends(get_db)):
    data = AccountingEntryClass(db).annul(entry_id)
    return {"message": data}


@accounting_accounts.get("/")
def list_accounts(db: Session = Depends(get_db)):
    data = AccountingEntryClass(db).list_accounts(active_only=True)
    return {"message": data}


@accounting_accounts.post("/")
def create_account(payload: AccountingAccountCreate, db: Session = Depends(get_db)):
    data = AccountingEntryClass(db).store_account(payload.code, payload.name)
    return {"message": data}
