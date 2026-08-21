from sqlalchemy import text
from app.backend.db.database import SessionLocal

db = SessionLocal()


def q(sql, **kw):
    rows = db.execute(text(sql), kw).mappings().all()
    return [dict(r) for r in rows]


def show(title, rows):
    print(f"\n=== {title} ===")
    for r in rows:
        print(r)


show("settings", q("SELECT id, accounting_backend FROM settings LIMIT 5"))

show(
    "eerr 2026-07 totals",
    q("SELECT COUNT(*) n, COALESCE(SUM(amount),0) amt FROM eerr WHERE period='2026-07'"),
)

show(
    "eerr top accounts",
    q(
        """
        SELECT accounting_account, COUNT(*) n, ROUND(SUM(amount),0) amt
        FROM eerr WHERE period='2026-07'
        GROUP BY accounting_account
        ORDER BY amt DESC
        LIMIT 25
        """
    ),
)

show(
    "remunerations periods recent",
    q(
        """
        SELECT period, COUNT(*) n, ROUND(COALESCE(SUM(amount),0),0) amt
        FROM remunerations
        GROUP BY period
        ORDER BY period DESC
        LIMIT 12
        """
    ),
)

show(
    "accounting_entries kinds 2026-07",
    q(
        """
        SELECT
          CASE
            WHEN glosa LIKE '%_Abonados%' THEN 'abonados'
            WHEN glosa LIKE '%BoletaFiscal%' THEN 'ingresos'
            WHEN glosa LIKE '%_Rendicion_%' THEN 'rendicion'
            WHEN glosa LIKE '%FacturaCompra_%' THEN 'factura_compra'
            WHEN glosa LIKE '%NotaCreditoCompra_%' THEN 'nc_compra'
            WHEN glosa LIKE '%Remuner%' THEN 'remuneracion_asiento'
            ELSE 'other'
          END AS kind,
          COUNT(*) AS entries,
          SUM(CASE WHEN annulled=0 THEN 1 ELSE 0 END) AS active
        FROM accounting_entries
        WHERE period='2026-07'
        GROUP BY kind
        ORDER BY kind
        """
    ),
)

show(
    "accounting_entries total july",
    q(
        """
        SELECT COUNT(*) n,
               SUM(CASE WHEN annulled=0 THEN 1 ELSE 0 END) active
        FROM accounting_entries
        WHERE period='2026-07'
        """
    ),
)

show(
    "sample non abonado/ingreso glosas",
    q(
        """
        SELECT id, LEFT(glosa,140) AS glosa, annulled, source
        FROM accounting_entries
        WHERE period='2026-07'
          AND glosa NOT LIKE '%_Abonados%'
          AND glosa NOT LIKE '%BoletaFiscal%'
        ORDER BY id DESC
        LIMIT 25
        """
    ),
)

show(
    "capitulations july by type/status",
    q(
        """
        SELECT document_type_id, status_id, COUNT(*) n
        FROM capitulations
        WHERE period IN ('2026-07','07-2026')
           OR (document_date >= '2026-07-01' AND document_date < '2026-08-01')
        GROUP BY document_type_id, status_id
        ORDER BY document_type_id, status_id
        """
    ),
)

show(
    "imputed capitulations non-39",
    q(
        """
        SELECT COUNT(*) imputed_non_boleta
        FROM capitulations
        WHERE status_id = 5
          AND document_type_id <> 39
          AND (
            period IN ('2026-07','07-2026')
            OR (document_date >= '2026-07-01' AND document_date < '2026-08-01')
          )
        """
    ),
)

show(
    "imputed capitulations boleta 39",
    q(
        """
        SELECT COUNT(*) imputed_boleta
        FROM capitulations
        WHERE status_id = 5
          AND document_type_id = 39
          AND (
            period IN ('2026-07','07-2026')
            OR (document_date >= '2026-07-01' AND document_date < '2026-08-01')
          )
        """
    ),
)

# received purchase docs - try dtes / received tables
for sql, title in [
    (
        """
        SELECT status_id, dte_type_id, COUNT(*) n
        FROM dtes
        WHERE dte_version_id = 2 AND period = '2026-07'
        GROUP BY status_id, dte_type_id
        ORDER BY status_id, dte_type_id
        """,
        "dtes v2 period 2026-07",
    ),
    (
        """
        SELECT status_id, COUNT(*) n
        FROM received_tributary_documents
        WHERE period = '2026-07'
           OR (added_date >= '2026-07-01' AND added_date < '2026-08-01')
        GROUP BY status_id
        """,
        "received_tributary_documents july",
    ),
]:
    try:
        show(title, q(sql))
    except Exception as e:
        print(f"\n=== {title} ERROR ===", e)
        db.rollback()

show(
    "rendicion/factura asientos any period recent",
    q(
        """
        SELECT period,
          SUM(glosa LIKE '%_Rendicion_%') rend,
          SUM(glosa LIKE '%FacturaCompra_%') fc,
          COUNT(*) total
        FROM accounting_entries
        WHERE period >= '2026-01'
        GROUP BY period
        ORDER BY period
        """
    ),
)

db.close()
print("\nDONE")
