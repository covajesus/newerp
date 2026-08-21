from sqlalchemy import text
from app.backend.db.database import SessionLocal

db = SessionLocal()


def q(sql):
    return [dict(r) for r in db.execute(text(sql)).mappings().all()]


print("active kinds", q(
    """
    SELECT
      CASE
        WHEN glosa LIKE '%_Rendicion_%' THEN 'rendicion'
        WHEN glosa LIKE '%FacturaCompra_%' THEN 'factura_compra'
        WHEN glosa LIKE '%NotaCreditoCompra_%' THEN 'nc_compra'
        WHEN glosa LIKE '%_Abonados%' THEN 'abonados'
        WHEN glosa LIKE '%BoletaFiscal%' THEN 'ingresos'
        ELSE 'other'
      END kind,
      source,
      COUNT(*) n
    FROM accounting_entries
    WHERE period='2026-07' AND annulled=0
    GROUP BY kind, source
    ORDER BY kind, source
    """
))

print("eerr key accounts", q(
    """
    SELECT accounting_account, COUNT(*) n, ROUND(SUM(amount),0) amt
    FROM eerr
    WHERE period='2026-07'
      AND accounting_account IN (
        '441000101','441000102','221000226','111000102',
        '443000302','443003437','443000357','443000322'
      )
    GROUP BY accounting_account
    ORDER BY accounting_account
    """
))

print("eerr totals", q("SELECT COUNT(*) n, ROUND(SUM(amount),0) amt FROM eerr WHERE period='2026-07'"))
print("dups", q(
    """
    SELECT COUNT(*) n FROM (
      SELECT glosa FROM accounting_entries
      WHERE period='2026-07' AND annulled=0
      GROUP BY glosa HAVING COUNT(*)>1
    ) t
    """
))
print("annulled imports", q(
    """
    SELECT COUNT(*) n FROM accounting_entries
    WHERE period='2026-07' AND source='libredte_import' AND annulled=1
    """
))

db.close()
