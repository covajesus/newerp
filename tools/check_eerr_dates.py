from sqlalchemy import text
from app.backend.db.database import SessionLocal

db = SessionLocal()


def q(sql):
    return [dict(r) for r in db.execute(text(sql)).mappings().all()]


print("EERR", q("SELECT MIN(added_date) a, MAX(added_date) b, COUNT(*) n FROM eerr WHERE period='2026-07'"))
print("AE", q("SELECT MIN(added_date) a, MAX(added_date) b, COUNT(*) n FROM accounting_entries WHERE period='2026-07'"))
print(
    "by kind",
    q(
        """
        SELECT
          CASE
            WHEN glosa LIKE '%_Rendicion_%' THEN 'rendicion'
            WHEN glosa LIKE '%FacturaCompra_%' THEN 'factura_compra'
            WHEN glosa LIKE '%_Abonados%' THEN 'abonados'
            WHEN glosa LIKE '%BoletaFiscal%' THEN 'ingresos'
            WHEN glosa LIKE '%NotaCreditoCompra_%' THEN 'nc_compra'
            ELSE 'other'
          END AS k,
          source,
          COUNT(*) AS n,
          MIN(added_date) AS a,
          MAX(added_date) AS b
        FROM accounting_entries
        WHERE period='2026-07'
        GROUP BY k, source
        ORDER BY k, source
        """
    ),
)
print(
    "arriendos eerr",
    q("SELECT COUNT(*) n, COALESCE(SUM(amount),0) amt FROM eerr WHERE period='2026-07' AND accounting_account='443000302'"),
)
print(
    "combustible eerr",
    q("SELECT COUNT(*) n FROM eerr WHERE period='2026-07' AND accounting_account='443003437'"),
)
print(
    "eerr row count vs remun",
    q("SELECT COUNT(*) eerr_n FROM eerr WHERE period='2026-07'"),
    q("SELECT COUNT(*) rem_n FROM remunerations WHERE period='2026-07'"),
)

# How many eerr rows are NOT from remun accounts pattern 443101
print(
    "eerr non-remun-like",
    q(
        """
        SELECT COUNT(*) n FROM eerr
        WHERE period='2026-07'
          AND accounting_account NOT LIKE '443101%'
          AND accounting_account NOT LIKE '443000499'
          AND accounting_account NOT LIKE '443000498'
        """
    ),
)

db.close()
