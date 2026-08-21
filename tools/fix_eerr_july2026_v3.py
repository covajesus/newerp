import time
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
)
from app.backend.classes.seat_class import SeatClass

PERIOD = "2026-07"


def wait_for_eerr_idle(max_wait=180):
    db = SessionLocal()
    try:
        for i in range(max_wait // 3):
            busy = db.execute(
                text(
                    """
                    SELECT Id, Time, State, LEFT(Info,100) Info
                    FROM information_schema.PROCESSLIST
                    WHERE INFO LIKE '%eerr%'
                      AND COMMAND != 'Sleep'
                      AND ID != CONNECTION_ID()
                    """
                )
            ).mappings().all()
            if not busy:
                print("eerr idle", flush=True)
                return True
            print("waiting for eerr ops:", [dict(b) for b in busy], flush=True)
            time.sleep(3)
            db.rollback()
        return False
    finally:
        db.close()


print("waiting...", flush=True)
ok = wait_for_eerr_idle()
if not ok:
    print("TIMEOUT waiting for locks", flush=True)

db = SessionLocal()

# Annul remaining same-source dups (keep lowest id)
print("annulling remaining factura dups", flush=True)
db.execute(
    text(
        """
        UPDATE accounting_entries ae
        INNER JOIN (
          SELECT glosa, MIN(id) keep_id
          FROM accounting_entries
          WHERE period=:p AND annulled=0
          GROUP BY glosa
          HAVING COUNT(*) > 1
        ) d ON d.glosa = ae.glosa
        SET ae.annulled = 1, ae.updated_date = :now
        WHERE ae.period = :p
          AND ae.annulled = 0
          AND ae.id <> d.keep_id
        """
    ),
    {"p": PERIOD, "now": datetime.now()},
)
db.commit()

dups = db.execute(
    text(
        """
        SELECT COUNT(*) FROM (
          SELECT glosa FROM accounting_entries
          WHERE period=:p AND annulled=0
          GROUP BY glosa HAVING COUNT(*) > 1
        ) t
        """
    ),
    {"p": PERIOD},
).scalar()
print("dups left:", dups, flush=True)

# Check if current eerr already has arriendos (maybe concurrent refresh finished)
arriendos = db.execute(
    text("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM eerr WHERE period=:p AND accounting_account='443000302'"),
    {"p": PERIOD},
).first()
print("current arriendos in eerr:", tuple(arriendos), flush=True)
eerr_n = db.execute(text("SELECT COUNT(*) FROM eerr WHERE period=:p"), {"p": PERIOD}).scalar()
print("current eerr rows:", eerr_n, flush=True)

need_refresh = (arriendos[0] or 0) == 0
if not need_refresh:
    print("EERR already has purchase expenses — skip rebuild", flush=True)
    db.close()
    print("DONE", flush=True)
    raise SystemExit(0)

print("=== rebuilding EERR ===", flush=True)
seat = SeatClass(db)

# delete with raw SQL + retry
for attempt in range(5):
    try:
        deleted = db.execute(text("DELETE FROM eerr WHERE period=:p"), {"p": PERIOD}).rowcount
        db.commit()
        print(f"deleted eerr rows: {deleted}", flush=True)
        break
    except Exception as exc:
        print(f"delete attempt {attempt+1} failed: {exc}", flush=True)
        db.rollback()
        time.sleep(5)
else:
    raise RuntimeError("Could not clear eerr")

branches = db.query(BranchOfficeModel).all()
branch_exact = {b.branch_office: b for b in branches if b.branch_office}
branch_norm = {seat.normalize_text(b.branch_office): b for b in branches if b.branch_office}
accounts = {str(a.code): (a.name or "").strip() for a in db.query(AccountingAccountModel).all()}
expense_by_account = {
    str(e.accounting_account): e
    for e in db.query(ExpenseTypeModel).all()
    if e.accounting_account
}

entries = (
    db.query(AccountingEntryModel)
    .filter(AccountingEntryModel.period == PERIOD, AccountingEntryModel.annulled == 0)
    .all()
)
print("active entries:", len(entries), flush=True)

processed_details = skipped = processed_seats = 0
batch = []
for entry in entries:
    glosa = entry.glosa or ""
    parts = glosa.split("_") if glosa else []
    search = parts[0] if parts else ""
    bo = branch_exact.get(search) or branch_norm.get(seat.normalize_text(search))
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
        batch.append(
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
        if len(batch) >= 200:
            db.add_all(batch)
            db.commit()
            batch = []
    processed_seats += 1

if batch:
    db.add_all(batch)
    db.commit()

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

print(
    "verify arriendos",
    db.execute(
        text(
            "SELECT COUNT(*) n, COALESCE(SUM(amount),0) amt FROM eerr WHERE period=:p AND accounting_account='443000302'"
        ),
        {"p": PERIOD},
    ).first(),
    flush=True,
)
print(
    "verify combustible",
    db.execute(
        text(
            "SELECT COUNT(*) n, COALESCE(SUM(amount),0) amt FROM eerr WHERE period=:p AND accounting_account='443003437'"
        ),
        {"p": PERIOD},
    ).first(),
    flush=True,
)
print(
    "eerr totals",
    db.execute(
        text("SELECT COUNT(*) n, COALESCE(SUM(amount),0) amt FROM eerr WHERE period=:p"),
        {"p": PERIOD},
    ).first(),
    flush=True,
)

db.close()
print("DONE", flush=True)
