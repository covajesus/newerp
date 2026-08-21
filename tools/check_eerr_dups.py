from sqlalchemy import text
from app.backend.db.database import SessionLocal

db = SessionLocal()


def q(sql):
    return [dict(r) for r in db.execute(text(sql)).mappings().all()]


print(
    "duplicate glosas system vs import",
    q(
        """
        SELECT COUNT(*) duplicate_glosas
        FROM (
          SELECT glosa
          FROM accounting_entries
          WHERE period='2026-07' AND annulled=0
          GROUP BY glosa
          HAVING COUNT(*) > 1
        ) t
        """
    ),
)

print(
    "dup samples",
    q(
        """
        SELECT glosa, GROUP_CONCAT(DISTINCT source) sources, COUNT(*) n,
               GROUP_CONCAT(id) ids
        FROM accounting_entries
        WHERE period='2026-07' AND annulled=0
        GROUP BY glosa
        HAVING COUNT(*) > 1
        LIMIT 15
        """
    ),
)

print(
    "counts by source",
    q(
        """
        SELECT source, COUNT(*) n
        FROM accounting_entries
        WHERE period='2026-07' AND annulled=0
        GROUP BY source
        """
    ),
)

print(
    "ingresos/abonados only in system (not duplicated)",
    q(
        """
        SELECT
          SUM(CASE WHEN glosa LIKE '%BoletaFiscal%' AND source='system' THEN 1 ELSE 0 END) ingresos_system,
          SUM(CASE WHEN glosa LIKE '%BoletaFiscal%' AND source='libredte_import' THEN 1 ELSE 0 END) ingresos_import,
          SUM(CASE WHEN glosa LIKE '%_Abonados%' AND source='system' THEN 1 ELSE 0 END) abon_system,
          SUM(CASE WHEN glosa LIKE '%_Abonados%' AND source='libredte_import' THEN 1 ELSE 0 END) abon_import,
          SUM(CASE WHEN glosa LIKE '%_Rendicion_%' THEN 1 ELSE 0 END) rend,
          SUM(CASE WHEN glosa LIKE '%FacturaCompra_%' THEN 1 ELSE 0 END) fc
        FROM accounting_entries
        WHERE period='2026-07' AND annulled=0
        """
    ),
)

db.close()
