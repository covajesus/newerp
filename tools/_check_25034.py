from dotenv import load_dotenv
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()
from sqlalchemy import text
from app.backend.db.database import SessionLocal
db = SessionLocal()
print("folio 25034 in folios?", db.execute(text("SELECT id, folio, dte_id, document_type_id, used_id FROM folios WHERE folio=25034")).fetchall())
print("folio 25122 in folios?", db.execute(text("SELECT id, folio, dte_id, document_type_id, used_id FROM folios WHERE folio=25122")).fetchall())
print("pending nc for 25034?", db.execute(text("SELECT id, folio, denied_folio, status_id, dte_type_id, rut FROM dtes WHERE denied_folio IN ('25034','25122','60803000') OR (dte_type_id=61 AND rut LIKE '%60803000%' AND status_id IN (14,4,5) AND added_date>='2026-07-01') ORDER BY id DESC LIMIT 15")).fetchall())
print("branch 35", db.execute(text("SELECT id, branch_office FROM branch_offices WHERE id=35")).fetchone())
db.close()
