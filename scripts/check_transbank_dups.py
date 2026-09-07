import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
url = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
eng = create_engine(url)
with eng.connect() as c:
    total = c.execute(
        text(
            "SELECT COUNT(*) FROM transbank_statements "
            "WHERE original_date LIKE '2026-09%'"
        )
    ).scalar()
    by_day = c.execute(
        text(
            "SELECT original_date, COUNT(*) c FROM transbank_statements "
            "WHERE original_date LIKE '2026-09%' "
            "GROUP BY original_date ORDER BY original_date"
        )
    ).fetchall()
    dups = c.execute(
        text(
            """
        SELECT code, original_date, card_number, value_3, amount, COUNT(*) c
        FROM transbank_statements
        WHERE original_date LIKE '2026-09%'
        GROUP BY code, original_date, card_number, value_3, amount
        HAVING COUNT(*) > 1
        ORDER BY c DESC
        LIMIT 30
        """
        )
    ).fetchall()
    dups2 = c.execute(
        text(
            """
        SELECT code, original_date, amount, sale_type, sale_description, COUNT(*) c
        FROM transbank_statements
        WHERE original_date LIKE '2026-09%'
        GROUP BY code, original_date, amount, sale_type, sale_description,
                 branch_office_name, payment_type, value_1, value_2, value_4
        HAVING COUNT(*) > 1
        ORDER BY c DESC
        LIMIT 20
        """
        )
    ).fetchall()
    empty_auth = c.execute(
        text(
            """
        SELECT
          SUM(CASE WHEN value_3 IS NULL OR value_3='' THEN 1 ELSE 0 END) empty_auth,
          SUM(CASE WHEN card_number IS NULL OR card_number='' THEN 1 ELSE 0 END) empty_card,
          COUNT(*) total
        FROM transbank_statements
        WHERE original_date LIKE '2026-09%'
        """
        )
    ).fetchone()
    extra_months = c.execute(
        text(
            """
        SELECT LEFT(original_date, 7) ym, COUNT(*) c
        FROM transbank_statements
        GROUP BY LEFT(original_date, 7)
        ORDER BY ym DESC
        LIMIT 6
        """
        )
    ).fetchall()
    print("TOTAL_SEP", total)
    print("BY_DAY", [tuple(r) for r in by_day])
    print("EMPTY_AUTH_CARD_TOTAL", tuple(empty_auth))
    print("DUP_KEY_GROUPS", len(dups))
    for r in dups[:15]:
        print("DUP", tuple(r))
    print("DUP_FULLROW_GROUPS", len(dups2))
    for r in dups2[:10]:
        print("DUP2", tuple(r))
    print("MONTHS", [tuple(r) for r in extra_months])
