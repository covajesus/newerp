from sqlalchemy import text
from app.backend.db.database import SessionLocal

db = SessionLocal()


def q(sql):
    return [dict(r) for r in db.execute(text(sql)).mappings().all()]


print("=== expense lines from rendicion/factura july ===")
rows = q(
    """
    SELECT aa.name, ael.account_code,
           SUM(ael.debit) debit, SUM(ael.credit) credit, COUNT(*) n
    FROM accounting_entries ae
    JOIN accounting_entry_lines ael ON ael.accounting_entry_id = ae.id
    LEFT JOIN accounting_accounts aa ON aa.code = ael.account_code
    WHERE ae.period='2026-07' AND ae.annulled=0
      AND (ae.glosa LIKE '%_Rendicion_%' OR ae.glosa LIKE '%FacturaCompra_%')
    GROUP BY aa.name, ael.account_code
    ORDER BY debit DESC
    LIMIT 40
    """
)
for r in rows:
    print(r)

print("\n=== those accounts in eerr? ===")
codes = [r["account_code"] for r in rows if r["account_code"]]
if codes:
    inlist = ",".join(f"'{c}'" for c in codes[:50])
    for r in q(
        f"""
        SELECT accounting_account, COUNT(*) n, ROUND(SUM(amount),0) amt
        FROM eerr
        WHERE period='2026-07' AND accounting_account IN ({inlist})
        GROUP BY accounting_account
        """
    ):
        print(r)

print("\n=== branch match failures for rend/fc ===")
for r in q(
    """
    SELECT ae.id, SUBSTRING_INDEX(ae.glosa, '_', 1) AS glosa_branch,
           bo.id AS matched_branch_id, LEFT(ae.glosa,100) glosa
    FROM accounting_entries ae
    LEFT JOIN branch_offices bo
      ON bo.branch_office = SUBSTRING_INDEX(ae.glosa, '_', 1)
    WHERE ae.period='2026-07'
      AND (ae.glosa LIKE '%_Rendicion_%' OR ae.glosa LIKE '%FacturaCompra_%')
      AND bo.id IS NULL
    LIMIT 30
    """
):
    print(r)

print("\n=== unmatched count ===")
print(
    q(
        """
        SELECT COUNT(*) unmatched
        FROM accounting_entries ae
        LEFT JOIN branch_offices bo
          ON bo.branch_office = SUBSTRING_INDEX(ae.glosa, '_', 1)
        WHERE ae.period='2026-07'
          AND (ae.glosa LIKE '%_Rendicion_%' OR ae.glosa LIKE '%FacturaCompra_%')
          AND bo.id IS NULL
        """
    )
)

print("\n=== matched count ===")
print(
    q(
        """
        SELECT COUNT(*) matched
        FROM accounting_entries ae
        JOIN branch_offices bo
          ON bo.branch_office = SUBSTRING_INDEX(ae.glosa, '_', 1)
        WHERE ae.period='2026-07'
          AND (ae.glosa LIKE '%_Rendicion_%' OR ae.glosa LIKE '%FacturaCompra_%')
        """
    )
)

print("\n=== eerr amount by source heuristic (join via account) ===")
# sample eerr rows that look like expenses (443*)
for r in q(
    """
    SELECT accounting_account, ROUND(SUM(amount),0) amt, COUNT(*) n
    FROM eerr
    WHERE period='2026-07' AND accounting_account LIKE '443%'
    GROUP BY accounting_account
    ORDER BY amt ASC
    LIMIT 30
    """
):
    print(r)

print("\n=== sample rendicion entry lines ===")
for r in q(
    """
    SELECT ae.id, LEFT(ae.glosa,90) glosa, ael.account_code, ael.debit, ael.credit, aa.name
    FROM accounting_entries ae
    JOIN accounting_entry_lines ael ON ael.accounting_entry_id = ae.id
    LEFT JOIN accounting_accounts aa ON aa.code = ael.account_code
    WHERE ae.period='2026-07' AND ae.glosa LIKE '%_Rendicion_%'
    ORDER BY ae.id DESC
    LIMIT 12
    """
):
    print(r)

db.close()
