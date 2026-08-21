from sqlalchemy import text
from app.backend.db.database import SessionLocal

db = SessionLocal()
rows = db.execute(text("SHOW FULL PROCESSLIST")).mappings().all()
print("=== processlist ===")
for r in rows:
    info = str(r.get("Info") or "")
    cmd = r.get("Command")
    if cmd == "Sleep" and "eerr" not in info.lower() and r.get("Time", 0) < 30:
        continue
    print(
        {
            "Id": r["Id"],
            "User": r["User"],
            "Time": r["Time"],
            "Command": cmd,
            "State": r.get("State"),
            "Info": info[:160],
        }
    )

print("\n=== remaining dups ===")
for x in db.execute(
    text(
        """
        SELECT glosa, GROUP_CONCAT(id) ids, GROUP_CONCAT(source) sources, COUNT(*) n
        FROM accounting_entries
        WHERE period='2026-07' AND annulled=0
        GROUP BY glosa
        HAVING COUNT(*) > 1
        """
    )
).mappings():
    print(dict(x))

db.close()
