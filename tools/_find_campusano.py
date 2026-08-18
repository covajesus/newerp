#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import text
from app.backend.db.database import SessionLocal

db = SessionLocal()
q = """
SELECT id, folio, denied_folio, dte_type_id, status_id, dte_version_id,
       branch_office_id, rut, total, cash_amount, card_amount, reason_id,
       comment, added_date, period
FROM dtes
WHERE REPLACE(REPLACE(LOWER(rut), '.', ''), ' ', '') LIKE :rut
ORDER BY id DESC
LIMIT 30
"""
rows = db.execute(text(q), {"rut": "%15335559%"}).fetchall()
print("DTES by rut:")
for r in rows:
    print(dict(r._mapping))

rows2 = db.execute(text("""
SELECT d.id, d.folio, d.denied_folio, d.dte_type_id, d.status_id, d.branch_office_id,
       d.rut, d.total, d.added_date, b.branch_office
FROM dtes d
LEFT JOIN branch_offices b ON b.id = d.branch_office_id
WHERE d.total IN (-65450, 65450, -65000, 65000)
  AND (d.rut LIKE '%15335559%' OR d.rut LIKE '%15.335.559%')
ORDER BY d.id DESC LIMIT 20
""")).fetchall()
print("--- amount match ---")
for r in rows2:
    print(dict(r._mapping))

# branch name
print("--- branch ---")
for r in db.execute(text("SELECT id, branch_office FROM branch_offices WHERE branch_office LIKE '%BANCOESTADO%' OR branch_office LIKE '%BANCO ESTADO%'")).fetchall():
    print(dict(r._mapping))
db.close()
