#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from collections import Counter
from io import StringIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from app.backend.classes.transbank_statement_class import TransbankStatementClass

DAT = r"tools\_tbk_extract\cartola-movimientos-20269(04-09-2026_08.33.03_278925).dat"
raw = open(DAT, "rb").read()
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
months = Counter()
samples = {}
for _, row in df.iterrows():
    d = TransbankStatementClass._parse_transbank_date(
        TransbankStatementClass._row_get(row, colmap, "fecha")
    )
    if not d:
        months["INVALID"] += 1
        continue
    key = d.strftime("%Y-%m")
    months[key] += 1
    samples.setdefault(key, d.strftime("%d/%m/%Y %H:%M:%S"))

print("by month:")
for k, v in sorted(months.items()):
    print(k, v, "sample", samples.get(k))
