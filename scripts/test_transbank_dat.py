from pathlib import Path
from io import StringIO
from datetime import date
import pandas as pd

from app.backend.classes.transbank_statement_class import TransbankStatementClass

path = Path(
    r"C:\Users\jesus\Downloads\cartola-movimientos-20269(04-09-2026_08.33.03_278925)"
    r"\cartola-movimientos-20269(04-09-2026_08.33.03_278925).dat"
)
raw = path.read_bytes()
content = TransbankStatementClass._decode_transbank_bytes(raw)
lines = content.splitlines()
idx = TransbankStatementClass._find_transbank_header_index(lines)
print("header_index", idx)
if idx is None:
    print("NO HEADER", TransbankStatementClass._transbank_file_preview(lines))
    raise SystemExit(1)

print("header", lines[idx][:220])
df = pd.read_csv(
    StringIO("\n".join(lines[idx:])),
    delimiter=";",
    dtype=str,
    index_col=False,
    quotechar='"',
)
df = df.fillna("")
df.columns = [
    str(c).replace("\ufeff", "").strip().strip('"').strip("'") for c in df.columns
]
print("columns", list(df.columns)[:15])
colmap = TransbankStatementClass._build_column_map(df.columns)
print("colmap", colmap)
print("rows", len(df))

min_d, max_d = date(2026, 9, 1), date(2026, 9, 30)
in_period = skipped = bad_date = no_local = 0
sample_dates = set()
for _, row in df.iterrows():
    local = TransbankStatementClass._row_get(row, colmap, "local_id")
    if not local:
        no_local += 1
        continue
    raw_date = TransbankStatementClass._row_get(row, colmap, "fecha")
    parsed = TransbankStatementClass._parse_transbank_date(raw_date)
    if not parsed:
        bad_date += 1
        continue
    sample_dates.add(parsed.date().isoformat())
    if parsed.date() < min_d or parsed.date() > max_d:
        skipped += 1
    else:
        in_period += 1

print("in_period", in_period, "out", skipped, "bad_date", bad_date, "no_local", no_local)
print(
    "date_range",
    min(sample_dates) if sample_dates else None,
    max(sample_dates) if sample_dates else None,
)
print("unique_dates", sorted(sample_dates))
