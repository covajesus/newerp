import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
url = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
eng = create_engine(url)
dte_id = 11809093
with eng.connect() as c:
    dte = c.execute(
        text(
            """
        SELECT id, folio, dte_type_id, rut, status_id, period, branch_office_id,
               dte_version_id, total, sii_status_id, sii_track_id, added_date
        FROM dtes WHERE id = :id
        """
        ),
        {"id": dte_id},
    ).mappings().first()
    print("DTE", dict(dte) if dte else None)
    if not dte:
        raise SystemExit(0)
    folio_row = c.execute(
        text(
            """
        SELECT id, dte_id, folio, document_type_id, status_id
        FROM folios WHERE dte_id = :id LIMIT 5
        """
        ),
        {"id": dte_id},
    ).mappings().all()
    print("FOLIOS_BY_DTE", [dict(r) for r in folio_row])
    if dte["folio"]:
        folio_by_num = c.execute(
            text(
                """
            SELECT id, dte_id, folio, document_type_id, status_id
            FROM folios WHERE folio = :f AND document_type_id IN (33,39) LIMIT 5
            """
            ),
            {"f": dte["folio"]},
        ).mappings().all()
        print("FOLIOS_BY_NUM", [dict(r) for r in folio_by_num])
        pay = c.execute(
            text("SELECT id, folio, order_id FROM dte_payment_data WHERE folio = :f LIMIT 5"),
            {"f": int(dte["folio"])},
        ).mappings().all()
        print("PAYMENT_DATA", [dict(r) for r in pay])
