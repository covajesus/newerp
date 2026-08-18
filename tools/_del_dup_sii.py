#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import text
from app.backend.db.database import SessionLocal

KEEP_RUT = "60803000-K"
DUP_ID = 10281
DUP_RUT = "60803000-0"

db = SessionLocal()
try:
    upd = db.execute(
        text("UPDATE dtes SET rut = :keep WHERE rut = :dup"),
        {"keep": KEEP_RUT, "dup": DUP_RUT},
    )
    print("dtes updated:", upd.rowcount)
    deleted = db.execute(
        text("DELETE FROM customers WHERE id = :id AND rut = :dup"),
        {"id": DUP_ID, "dup": DUP_RUT},
    )
    print("customers deleted:", deleted.rowcount)
    db.commit()
    print("remaining customers:")
    for r in db.execute(text("""
        SELECT id, rut, customer FROM customers
        WHERE REPLACE(REPLACE(REPLACE(UPPER(rut),'.',''),' ',''),'-','') LIKE '60803000%'
    """)).fetchall():
        print(dict(r._mapping))
    print("dtes still on -0:", db.execute(text("SELECT COUNT(*) FROM dtes WHERE rut=:r"), {"r": DUP_RUT}).fetchone()[0])
finally:
    db.close()
