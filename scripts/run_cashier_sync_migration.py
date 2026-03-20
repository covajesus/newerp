"""
Ejecuta migrations/create_cashier_sync_commands.sql usando las credenciales del .env (misma que la app).

Uso (desde la raíz del proyecto):
    python scripts/run_cashier_sync_migration.py
"""
import sys
from pathlib import Path

# Al ejecutar este archivo, sys.path[0] es scripts/; hay que añadir la raíz del repo
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from sqlalchemy import text


def main() -> None:
    from app.backend.db.database import engine  # noqa: WPS433 — tras load_dotenv

    sql_path = ROOT / "migrations" / "create_cashier_sync_commands.sql"
    sql = sql_path.read_text(encoding="utf-8")
    with engine.begin() as conn:
        conn.execute(text(sql))
    print("OK: tabla cashier_sync_commands creada (o ya existía).")


if __name__ == "__main__":
    main()
