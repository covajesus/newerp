#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from io import StringIO
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from sqlalchemy import text
from app.backend.classes.transbank_statement_class import TransbankStatementClass
from app.backend.db.database import SessionLocal

DAT = r"tools\_tbk_extract\cartola-movimientos-20269(04-09-2026_08.33.03_278925).dat"


def main():
    with open(DAT, "rb") as f:
        raw = f.read()
    content = TransbankStatementClass._decode_transbank_bytes(raw)
    lines = content.splitlines()
    idx = TransbankStatementClass._find_transbank_header_index(lines)
    df = pd.read_csv(
        StringIO("\n".join(lines[idx:])),
        delimiter=";",
        dtype=str,
        index_col=False,
        quotechar='"',
    ).fillna("")
    df.columns = [
        str(c).replace("\ufeff", "").strip().strip('"').strip("'") for c in df.columns
    ]
    colmap = TransbankStatementClass._build_column_map(df.columns)
    print("rows", len(df), "header_ok", idx is not None)

    codes = Counter()
    names = {}
    for _, row in df.iterrows():
        code = TransbankStatementClass._row_get(row, colmap, "local_id")
        name = TransbankStatementClass._row_get(row, colmap, "local_name")
        if code:
            codes[code] += 1
            names[code] = name

    db = SessionLocal()
    try:
        mapped = []
        unmapped = []
        for code, n in codes.most_common():
            row = db.execute(
                text(
                    "SELECT transbank_code, branch_office_id, status "
                    "FROM branch_offices_transbanks WHERE transbank_code = :c LIMIT 1"
                ),
                {"c": code},
            ).fetchone()
            if row:
                mapped.append((code, n, names[code], dict(row._mapping)))
            else:
                unmapped.append((code, n, names[code]))

        print("unique codes", len(codes))
        print("mapped", len(mapped), "rows", sum(x[1] for x in mapped))
        print("unmapped", len(unmapped), "rows", sum(x[1] for x in unmapped))
        print("--- UNMAPPED (these are silently skipped) ---")
        for code, n, name in unmapped:
            print(f"{code}\t{n}\t{name}")
        print("--- MAPPED sample ---")
        for code, n, name, info in mapped[:10]:
            print(f"{code}\t{n}\t{name}\tbranch={info['branch_office_id']}\tstatus={info.get('status')}")

        # also check if period already has data / was wiped
        c = db.execute(
            text(
                "SELECT COUNT(*) AS c FROM transbank_statements "
                "WHERE original_date BETWEEN '2026-09-01' AND '2026-09-30'"
            )
        ).fetchone()[0]
        print("existing sep2026 rows in DB:", c)
    finally:
        db.close()


if __name__ == "__main__":
    main()
