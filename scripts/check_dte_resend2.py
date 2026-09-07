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
    print(
        "FOLIOS_DTE",
        [dict(r) for r in c.execute(text("SELECT id,dte_id,folio,document_type_id FROM folios WHERE dte_id=11809093 LIMIT 5")).mappings()],
    )
    print(
        "FOLIOS_NUM",
        [dict(r) for r in c.execute(text("SELECT id,dte_id,folio,document_type_id FROM folios WHERE folio=25402 AND document_type_id=33 LIMIT 5")).mappings()],
    )
    print(
        "PAY",
        [dict(r) for r in c.execute(text("SELECT id,folio FROM dte_payment_data WHERE folio=25402 LIMIT 5")).mappings()],
    )
