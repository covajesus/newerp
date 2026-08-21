"""Inspect DTE/honorary history for RUT 27141399-8."""
from sqlalchemy import text
from app.backend.db.database import SessionLocal

RUT_VARIANTS = ("27141399-8", "271413998", "27.141.399-8")

db = SessionLocal()
try:
    print("=== honoraries ===")
    rows = db.execute(
        text(
            """
            SELECT id, replacement_employee_rut, foreigner_id, status_id, bte_emitted, bte_folio, added_date
            FROM honoraries
            WHERE REPLACE(REPLACE(CAST(replacement_employee_rut AS CHAR), '.', ''), '-', '') LIKE '%27141399%'
               OR CAST(replacement_employee_rut AS CHAR) LIKE '%27141399%'
            ORDER BY id DESC
            LIMIT 30
            """
        )
    ).mappings().all()
    for r in rows:
        print(dict(r))
    print(f"count={len(rows)}")

    print("\n=== dtes (boletas/facturas) receptor ===")
    rows2 = db.execute(
        text(
            """
            SELECT id, dte_type_id, folio, status_id, dte_version_id, total, period, added_date, rut
            FROM dtes
            WHERE REPLACE(REPLACE(CAST(rut AS CHAR), '.', ''), '-', '') LIKE '%27141399%'
            ORDER BY id DESC
            LIMIT 40
            """
        )
    ).mappings().all()
    for r in rows2:
        print(dict(r))
    print(f"count={len(rows2)}")

    print("\n=== dtes emitidos con folio>0 tipo 39 ===")
    rows3 = db.execute(
        text(
            """
            SELECT COUNT(*) AS n, MIN(folio) AS min_folio, MAX(folio) AS max_folio
            FROM dtes
            WHERE REPLACE(REPLACE(CAST(rut AS CHAR), '.', ''), '-', '') LIKE '%27141399%'
              AND dte_type_id = 39
              AND folio > 0
            """
        )
    ).mappings().first()
    print(dict(rows3) if rows3 else None)
finally:
    db.close()
