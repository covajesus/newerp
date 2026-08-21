from datetime import datetime
from sqlalchemy import text
from app.backend.db.database import SessionLocal
from app.backend.db.models import (
    AccountingEntryModel,
    AccountingEntryLineModel,
    AccountingAccountModel,
    ExpenseTypeModel,
    BranchOfficeModel,
    EerrModel,
    RemunerationModel,
)
from app.backend.classes.seat_class import SeatClass

PERIOD = "2026-07"
db = SessionLocal()


def q(sql, **kw):
    return [dict(r) for r in db.execute(text(sql), kw).mappings().all()]


print("=== current state ===", flush=True)
print(
    q(
        """
        SELECT source,
               SUM(CASE WHEN annulled=0 THEN 1 ELSE 0 END) AS active,
               SUM(CASE WHEN annulled=1 THEN 1 ELSE 0 END) AS ann
        FROM accounting_entries
        WHERE period=:p
        GROUP BY source
        """,
        p=PERIOD,
    ),
    flush=True,
)

dups = q(
    """
    SELECT COUNT(*) AS n FROM (
      SELECT glosa FROM accounting_entries
      WHERE period=:p AND annulled=0
      GROUP BY glosa HAVING COUNT(*) > 1
    ) t
    """,
    p=PERIOD,
)[0]["n"]
print("active duplicate glosas:", dups, flush=True)

if dups and dups > 0:
    result = db.execute(
        text(
            """
            UPDATE accounting_entries ae
            INNER JOIN accounting_entries sys
              ON sys.glosa = ae.glosa
             AND sys.period = ae.period
             AND sys.source = 'system'
             AND sys.annulled = 0
            SET ae.annulled = 1,
                ae.updated_date = :now
            WHERE ae.period = :p
              AND ae.source = 'libredte_import'
              AND ae.annulled = 0
            """
        ),
        {"p": PERIOD, "now": datetime.now()},
    )
    db.commit()
    print("Annulled duplicate import rows:", result.rowcount, flush=True)
else:
    print("No active duplicates to annul", flush=True)

# Fast EERR rebuild with cached branches (same logic as SeatClass, less N+1)
print("=== fast EERR refresh ===", flush=True)
seat = SeatClass(db)
seat.clear_existing_data(PERIOD)

branches = db.query(BranchOfficeModel).all()
branch_exact = {b.branch_office: b for b in branches if b.branch_office}
branch_norm = {seat.normalize_text(b.branch_office): b for b in branches if b.branch_office}

accounts = {
    str(a.code): (a.name or "").strip()
    for a in db.query(AccountingAccountModel).all()
}
expense_by_account = {
    str(e.accounting_account): e
    for e in db.query(ExpenseTypeModel).all()
    if e.accounting_account
}

entries = (
    db.query(AccountingEntryModel)
    .filter(
        AccountingEntryModel.period == PERIOD,
        AccountingEntryModel.annulled == 0,
    )
    .all()
)
print(f"active entries: {len(entries)}", flush=True)

processed_details = 0
skipped = 0
processed_seats = 0

for entry in entries:
    glosa = entry.glosa or ""
    parts = glosa.split("_") if glosa else []
    search = parts[0] if parts else ""
    bo = branch_exact.get(search)
    if not bo:
        bo = branch_norm.get(seat.normalize_text(search))
    if not bo:
        skipped += 1
        continue

    lines = (
        db.query(AccountingEntryLineModel)
        .filter(AccountingEntryLineModel.accounting_entry_id == entry.id)
        .order_by(AccountingEntryLineModel.sort_order.asc())
        .all()
    )
    for line in lines:
        code = str(line.account_code or "").strip()
        if not code:
            skipped += 1
            continue
        concept = (line.concept or "").strip()
        name = accounts.get(code, "")
        if concept == "Banco" or name == "Banco":
            skipped += 1
            continue
        et = expense_by_account.get(code)
        amount = seat.calculate_amount(
            {"debe": line.debit or "", "haber": line.credit or ""},
            et,
            glosa,
        )
        if not amount:
            skipped += 1
            continue
        db.add(
            EerrModel(
                branch_office_id=bo.id,
                seat_id=entry.number,
                period=PERIOD,
                accounting_account=code,
                amount=int(amount),
                added_date=datetime.now(),
                updated_date=datetime.now(),
            )
        )
        processed_details += 1
    processed_seats += 1

rem_count = seat.process_remunerations(PERIOD)
db.commit()

print(
    {
        "processed_seats": processed_seats,
        "processed_details": processed_details,
        "remunerations": rem_count,
        "skipped": skipped,
    },
    flush=True,
)

print("=== verify ===", flush=True)
print("eerr totals", q("SELECT COUNT(*) n, COALESCE(SUM(amount),0) amt FROM eerr WHERE period=:p", p=PERIOD), flush=True)
print(
    "arriendos",
    q(
        "SELECT COUNT(*) n, COALESCE(SUM(amount),0) amt FROM eerr WHERE period=:p AND accounting_account='443000302'",
        p=PERIOD,
    ),
    flush=True,
)
print(
    "combustible",
    q(
        "SELECT COUNT(*) n, COALESCE(SUM(amount),0) amt FROM eerr WHERE period=:p AND accounting_account='443003437'",
        p=PERIOD,
    ),
    flush=True,
)
print(
    "top 443000",
    q(
        """
        SELECT accounting_account, COUNT(*) n, ROUND(SUM(amount),0) amt
        FROM eerr WHERE period=:p AND accounting_account LIKE '443000%'
        GROUP BY accounting_account ORDER BY amt ASC LIMIT 12
        """,
        p=PERIOD,
    ),
    flush=True,
)
print(
    "active kinds",
    q(
        """
        SELECT
          CASE
            WHEN glosa LIKE '%_Rendicion_%' THEN 'rendicion'
            WHEN glosa LIKE '%FacturaCompra_%' THEN 'factura_compra'
            WHEN glosa LIKE '%_Abonados%' THEN 'abonados'
            WHEN glosa LIKE '%BoletaFiscal%' THEN 'ingresos'
            ELSE 'other'
          END AS kind,
          COUNT(*) n
        FROM accounting_entries
        WHERE period=:p AND annulled=0
        GROUP BY kind
        """,
        p=PERIOD,
    ),
    flush=True,
)
print(
    "dups left",
    q(
        """
        SELECT COUNT(*) n FROM (
          SELECT glosa FROM accounting_entries
          WHERE period=:p AND annulled=0
          GROUP BY glosa HAVING COUNT(*) > 1
        ) t
        """,
        p=PERIOD,
    ),
    flush=True,
)

db.close()
print("DONE", flush=True)
