#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from io import StringIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from app.backend.classes.transbank_statement_class import TransbankStatementClass
from app.backend.db.database import SessionLocal

DAT = r"C:\Users\jesus\Desktop\proyecto_jisparking\escritorio\newerp\tools\_tbk_extract\cartola-movimientos-20269(04-09-2026_08.33.03_278925).dat"

def main():
    with open(DAT, "rb") as f:
        raw = f.read()
    content = TransbankStatementClass._decode_transbank_bytes(raw)
    lines = content.splitlines()
    print("lines:", len(lines))
    idx = TransbankStatementClass._find_transbank_header_index(lines)
    print("header_index:", idx)
    if idx is None:
        print("NO HEADER")
        print(TransbankStatementClass._transbank_file_preview(lines))
        return
    print("HEADER:", lines[idx][:300])
    data_lines = "\n".join(lines[idx:])
    df = pd.read_csv(StringIO(data_lines), delimiter=";", dtype=str, index_col=False, quotechar='"')
    df = df.fillna("")
    df.columns = [str(c).replace("\ufeff", "").strip().strip('"').strip("'") for c in df.columns]
    print("columns:", list(df.columns))
    colmap = TransbankStatementClass._build_column_map(df.columns)
    print("colmap:", colmap)
    print("rows:", len(df))
    print("sample0:", {k: TransbankStatementClass._row_get(df.iloc[0], colmap, k) for k in colmap})
    # try parse date/amount
    d = TransbankStatementClass._parse_transbank_date(TransbankStatementClass._row_get(df.iloc[0], colmap, "fecha"))
    a = TransbankStatementClass._parse_amount(TransbankStatementClass._row_get(df.iloc[0], colmap, "monto_afecto"))
    print("parsed date:", d, "amount:", a)

    # full store
    db = SessionLocal()
    try:
        cls = TransbankStatementClass(db)
        # use local file path via file:// hack? better call with custom path by patching
        # Directly invoke processing using local content path through FileClass is hard.
        # Simulate store core path by temporarily monkeypatching download? Or call with fake local URL after copying.
        from app.backend.classes.file_class import FileClass
        remote = "transbank_statements_test_upload.dat"
        # write into files dir if exists
        files_dir = None
        for cand in ["files", "app/files", "static/files"]:
            if os.path.isdir(cand):
                files_dir = cand
                break
        print("files_dir:", files_dir)
        if files_dir:
            dest = os.path.join(files_dir, remote)
            with open(dest, "wb") as out:
                out.write(raw)
            url = f"http://127.0.0.1:8000/files/{remote}"
            print("calling read_store_bank_statement period=2026-09")
            def prog(p, m):
                print(f"[{p}] {m}")
            result = cls.read_store_bank_statement(url, "2026-09", progress_callback=prog)
            print("RESULT:", result)
        else:
            print("No local files dir; skip DB insert. Parse OK.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
