from sqlalchemy import text
from app.backend.db.database import SessionLocal
from app.backend.classes.seat_class import SeatClass
from app.backend.db.models import AccountingEntryLineModel, ExpenseTypeModel, AccountingEntryModel

db = SessionLocal()


def q(sql):
    return [dict(r) for r in db.execute(text(sql)).mappings().all()]


print("=== eerr dates ===")
print(q(
    """
    SELECT MIN(added_date) min_add, MAX(added_date) max_add,
           MIN(updated_date) min_upd, MAX(updated_date) max_upd, COUNT(*) n
    FROM eerr WHERE period='2026-07'
    """
))

print("\n=== entry dates columns ===")
print(q("SHOW COLUMNS FROM accounting_entries LIKE '%date%'"))
print(q("SHOW COLUMNS FROM accounting_entries LIKE '%source%'"))

print("\n=== entries by kind/source ===")
print(q(
    """
    SELECT source,
      CASE
        WHEN glosa LIKE '%_Abonados%' THEN 'abonados'
        WHEN glosa LIKE '%BoletaFiscal%' THEN 'ingresos'
        WHEN glosa LIKE '%_Rendicion_%' THEN 'rendicion'
        WHEN glosa LIKE '%FacturaCompra_%' THEN 'factura_compra'
        WHEN glosa LIKE '%NotaCreditoCompra_%' THEN 'nc_compra'
        ELSE 'other'
      END kind,
      COUNT(*) n,
      MIN(entry_date) min_entry,
      MAX(entry_date) max_entry,
      MIN(added_date) min_add,
      MAX(added_date) max_add
    FROM accounting_entries
    WHERE period='2026-07'
    GROUP BY source, kind
    ORDER BY kind, source
    """
))

seat = SeatClass(db)
entry = (
    db.query(AccountingEntryModel)
    .filter(
        AccountingEntryModel.period == "2026-07",
        AccountingEntryModel.glosa.like("%FacturaCompra_%"),
    )
    .order_by(AccountingEntryModel.id.desc())
    .first()
)
print("\n=== sample factura ===", entry.id, entry.glosa, entry.number, entry.source, entry.added_date)

bo = seat.find_branch_office((entry.glosa or "").split("_"))
print("branch", getattr(bo, "branch_office", None))
for line in db.query(AccountingEntryLineModel).filter(
    AccountingEntryLineModel.accounting_entry_id == entry.id
).all():
    is_banco = seat._is_banco_line(str(line.account_code), line.concept)
    et = (
        db.query(ExpenseTypeModel)
        .filter(ExpenseTypeModel.accounting_account == str(line.account_code))
        .first()
    )
    detail = {"debe": line.debit or "", "haber": line.credit or ""}
    amt = seat.calculate_amount(detail, et, entry.glosa)
    print(
        line.account_code,
        "deb",
        line.debit,
        "cred",
        line.credit,
        "banco?",
        is_banco,
        "amt",
        amt,
        "skip",
        is_banco or (not amt),
        "et",
        getattr(et, "expense_type", None),
        "pn",
        getattr(et, "positive_negative_id", None),
    )

# Simulate full would-insert for rend+fc
would = skip_banco = skip_amt = skip_bo = 0
sample_codes = {}
entries = (
    db.query(AccountingEntryModel)
    .filter(
        AccountingEntryModel.period == "2026-07",
        AccountingEntryModel.annulled == 0,
    )
    .filter(
        (AccountingEntryModel.glosa.like("%_Rendicion_%"))
        | (AccountingEntryModel.glosa.like("%FacturaCompra_%"))
    )
    .all()
)
for e in entries:
    bo = seat.find_branch_office((e.glosa or "").split("_"))
    if not bo:
        skip_bo += 1
        continue
    for line in (
        db.query(AccountingEntryLineModel)
        .filter(AccountingEntryLineModel.accounting_entry_id == e.id)
        .all()
    ):
        if seat._is_banco_line(str(line.account_code), line.concept):
            skip_banco += 1
            continue
        et = (
            db.query(ExpenseTypeModel)
            .filter(ExpenseTypeModel.accounting_account == str(line.account_code))
            .first()
        )
        amt = seat.calculate_amount(
            {"debe": line.debit or "", "haber": line.credit or ""},
            et,
            e.glosa or "",
        )
        if not amt:
            skip_amt += 1
            continue
        would += 1
        sample_codes[str(line.account_code)] = sample_codes.get(str(line.account_code), 0) + 1

print("\n=== sim rend/fc ===", {"would": would, "skip_banco": skip_banco, "skip_amt": skip_amt, "skip_bo": skip_bo})
print("top codes", sorted(sample_codes.items(), key=lambda x: -x[1])[:10])

# Are Arriendos missing because eerr refresh is stale?
print("\n=== arriendos in eerr? ===")
print(q("SELECT COUNT(*) n, COALESCE(SUM(amount),0) amt FROM eerr WHERE period='2026-07' AND accounting_account='443000302'"))

db.close()
