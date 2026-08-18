#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import text
from app.backend.db.database import SessionLocal

db = SessionLocal()
print("--- folios linked ---")
for r in db.execute(text("""
SELECT id, folio, dte_id, used_id, document_type_id, branch_office_id
FROM folios
WHERE dte_id IN (11806644, 11806289)
   OR folio IN (32679382, 6975)
ORDER BY id DESC LIMIT 20
""")).fetchall():
    print(dict(r._mapping))

print("--- next unused 61 ---")
print(dict(db.execute(text("""
SELECT id, folio, used_id, dte_id, branch_office_id
FROM folios
WHERE document_type_id=61 AND used_id=0 AND branch_office_id=0
ORDER BY folio ASC LIMIT 1
""")).mappings().first() or {}))

print("--- recent used 61 ---")
for r in db.execute(text("""
SELECT id, folio, used_id, dte_id, branch_office_id, updated_date
FROM folios
WHERE document_type_id=61 AND used_id=1
ORDER BY id DESC LIMIT 8
""")).fetchall():
    print(dict(r._mapping))
db.close()
