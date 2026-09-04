#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import text
from app.backend.db.database import SessionLocal

db = SessionLocal()
rows = db.execute(text(
    "SELECT LEFT(original_date,7) AS m, COUNT(*) AS c "
    "FROM transbank_statements GROUP BY LEFT(original_date,7) "
    "ORDER BY m DESC LIMIT 12"
)).fetchall()
print("months:")
for r in rows:
    print(r[0], r[1])
db.close()
