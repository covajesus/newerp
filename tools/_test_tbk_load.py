#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.backend.classes.transbank_statement_class import TransbankStatementClass
from app.backend.classes.file_class import FileClass
from app.backend.db.database import SessionLocal

DAT = r"tools\_tbk_extract\cartola-movimientos-20269(04-09-2026_08.33.03_278925).dat"


def main():
    db = SessionLocal()
    try:
        fc = FileClass(db)
        print("files_dir", fc.files_dir)
        remote = "transbank_statements_test_sep2026.dat"
        dest = os.path.join(fc.files_dir, remote)
        os.makedirs(fc.files_dir, exist_ok=True)
        with open(DAT, "rb") as src, open(dest, "wb") as out:
            out.write(src.read())
        print("copied", dest, os.path.getsize(dest))
        url = fc.get(remote)
        print("url", url)

        cls = TransbankStatementClass(db)

        def prog(p, m):
            print(f"[{p}] {m}")

        result = cls.read_store_bank_statement(url, "2026-09", progress_callback=prog)
        print("RESULT", result)
        n = db.execute(
            text(
                "SELECT COUNT(*) AS c FROM transbank_statements "
                "WHERE original_date BETWEEN '2026-09-01' AND '2026-09-30'"
            )
        ).fetchone()[0]
        print("rows in sep 2026:", n)
    except Exception as e:
        print("ERROR", type(e).__name__, e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
