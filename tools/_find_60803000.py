#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import text
from app.backend.db.database import SessionLocal

db = SessionLocal()
print("--- dtes rut like 60803000 ---")
for r in db.execute(text("""
SELECT id, folio, denied_folio, dte_type_id, status_id, dte_version_id,
       branch_office_id, rut, total, cash_amount, reason_id, comment, added_date, period
FROM dtes
WHERE REPLACE(REPLACE(REPLACE(LOWER(rut),'.',''),' ',''),'-','') LIKE '60803000%'
ORDER BY id DESC LIMIT 25
""")).fetchall():
    print(dict(r._mapping))

print("--- customers ---")
for r in db.execute(text("""
SELECT id, rut, customer FROM customers
WHERE REPLACE(REPLACE(REPLACE(LOWER(rut),'.',''),' ',''),'-','') LIKE '60803000%'
LIMIT 10
""")).fetchall():
    print(dict(r._mapping))

print("--- folios for those dtes ---")
for r in db.execute(text("""
SELECT f.id, f.folio, f.dte_id, f.document_type_id, f.used_id
FROM folios f
WHERE f.dte_id IN (
  SELECT id FROM dtes
  WHERE REPLACE(REPLACE(REPLACE(LOWER(rut),'.',''),' ',''),'-','') LIKE '60803000%'
)
ORDER BY f.id DESC LIMIT 20
""")).fetchall():
    print(dict(r._mapping))
db.close()
