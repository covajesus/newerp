from sqlalchemy import text
from app.backend.db.database import SessionLocal
from app.backend.db.models import ExpenseTypeModel
from app.backend.classes.accounting_entry_class import AccountingEntryClass

db = SessionLocal()
try:
    # Seed accounts from expense_types.accounting_account
    rows = (
        db.query(ExpenseTypeModel.accounting_account, ExpenseTypeModel.expense_type)
        .filter(ExpenseTypeModel.accounting_account.isnot(None))
        .all()
    )
    added = 0
    for code, name in rows:
        code = str(code or "").strip()
        if not code:
            continue
        name = str(name or code).strip() or code
        exists = db.execute(
            text("SELECT id FROM accounting_accounts WHERE code = :code"),
            {"code": code},
        ).first()
        if exists:
            continue
        db.execute(
            text(
                "INSERT INTO accounting_accounts "
                "(code, name, status_id, added_date, updated_date) "
                "VALUES (:code, :name, 1, NOW(), NOW())"
            ),
            {"code": code, "name": name},
        )
        added += 1
    db.commit()
    total = db.execute(text("SELECT COUNT(*) FROM accounting_accounts")).scalar()
    print(f"seeded_from_expense_types={added} total_accounts={total}")
    print("backend", AccountingEntryClass(db).get_backend())
    print("sync_method", hasattr(AccountingEntryClass(db), "sync_local_annul_after_libredte_delete"))
finally:
    db.close()
