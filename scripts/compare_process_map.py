"""Compare APIRouter prefixes vs BACKEND_ROUTE_PROCESS_MAP."""
import re
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

root = pathlib.Path(__file__).resolve().parents[1] / "app" / "backend" / "routers"
prefixes = set()
for f in root.glob("*.py"):
    t = f.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r"prefix\s*=\s*['\"](/[^'\"]+)['\"]", t):
        prefixes.add(m.group(1))

from app.backend.classes.process_registry import BACKEND_ROUTE_PROCESS_MAP

mapped = {p for p, _, _ in BACKEND_ROUTE_PROCESS_MAP}
missing = sorted(prefixes - mapped)
print("ROUTER PREFIXES", len(prefixes))
print("MAPPED", len(mapped))
print("MISSING FROM MAP:")
for p in missing:
    print(" ", p)
