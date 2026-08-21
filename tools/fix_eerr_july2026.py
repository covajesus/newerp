"""Annul duplicate July 2026 asientos (keep system), then refresh EERR."""
from datetime import datetime
from sqlalchemy import text
from app.backend.db.database import SessionLocal
from app.backend.classes.seat_class import SeatClass

PERIOD = "2026-07"
db = SessionLocal()


def q(sql, **kw):
    return [dict(r) for r in db.execute(text(sql), kw).mappings().all()]


print("=== before ===")
print(
    q(
        """
        SELECT source, COUNT(*) n,
          SUM(CASE WHEN annulled=0 THEN 1 ELSE 0 END) active
        FROM accounting_entries
        WHERE period=:p
        GROUP BY source
        """,
        p=PERIOD,
    )
)

# Annul libredte_import rows whose glosa already exists as active system row
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
print(f"Annulled duplicate import rows: {result.rowcount}")

print("=== after annul ===")
print(
    q(
        """
        SELECT
          CASE
            WHEN glosa LIKE '%_Rendicion_%' THEN 'rendicion'
            WHEN glosa LIKE '%FacturaCompra_%' THEN 'factura_compra'
            WHEN glosa LIKE '%NotaCreditoCompra_%' THEN 'nc_compra'
            WHEN glosa LIKE '%_Abonados%' THEN 'abonados'
            WHEN glosa LIKE '%BoletaFiscal%' THEN 'ingresos'
            ELSE 'other'
          END AS kind,
          source,
          SUM(CASE WHEN annulled=0 THEN 1 ELSE 0 END) AS active,
          SUM(CASE WHEN annulled=1 THEN 1 ELSE 0 END) AS annulled
        FROM accounting_entries
        WHERE period=:p
        GROUP BY kind, source
        ORDER BY kind, source
        """,
        p=PERIOD,
    )
)

dup_left = q(
    """
    SELECT COUNT(*) n FROM (
      SELECT glosa FROM accounting_entries
      WHERE period=:p AND annulled=0
      GROUP BY glosa HAVING COUNT(*) > 1
    ) t
    """,
    p=PERIOD,
)
print("active duplicate glosas left:", dup_left)

print("\n=== refreshing EERR 2026-07 ===")
# mute noisy branch prints
import builtins
_real_print = builtins.print

def _quiet_print(*args, **kwargs):
    msg = " ".join(str(a) for a in args)
    if msg.startswith("Buscando sucursal") or msg.startswith("No se encontró sucursal"):
        return
    _real_print(*args, **kwargs)

builtins.print = _quiet_print
try:
    result = SeatClass(db).refresh(
        external_token="",
        rut="",
        password="",
        month=7,
        year=2026,
    )
finally:
    builtins.print = _real_print

print("refresh result:", result)

print("\n=== verify EERR ===")
print("totals", q("SELECT COUNT(*) n, COALESCE(SUM(amount),0) amt FROM eerr WHERE period=:p", p=PERIOD))
print(
    "arriendos",
    q(
        "SELECT COUNT(*) n, COALESCE(SUM(amount),0) amt FROM eerr WHERE period=:p AND accounting_account='443000302'",
        p=PERIOD,
    ),
)
print(
    "combustible",
    q(
        "SELECT COUNT(*) n, COALESCE(SUM(amount),0) amt FROM eerr WHERE period=:p AND accounting_account='443003437'",
        p=PERIOD,
    ),
)
print(
    "top expense-like",
    q(
        """
        SELECT accounting_account, COUNT(*) n, ROUND(SUM(amount),0) amt
        FROM eerr
        WHERE period=:p AND accounting_account LIKE '443000%'
        GROUP BY accounting_account
        ORDER BY amt ASC
        LIMIT 15
        """,
        p=PERIOD,
    ),
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
)

db.close()
print("DONE")
