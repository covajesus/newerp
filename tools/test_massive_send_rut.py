"""Prueba envío masivo (send_massive_dtes_streaming) para un RUT / sucursal."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from app.backend.db.database import SessionLocal
from app.backend.classes.dte_class import DteClass

# branch 16, boleta 39 — única pendiente RUT 27141399-8 en 2026-07
BRANCH_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 16
DTE_TYPE = int(sys.argv[2]) if len(sys.argv) > 2 else 39
TARGET_RUT = sys.argv[3] if len(sys.argv) > 3 else "27141399-8"


def main() -> None:
    db = SessionLocal()
    try:
        dte_class = DteClass(db)
        events = []
        for event in dte_class.send_massive_dtes_streaming(BRANCH_ID, DTE_TYPE):
            events.append(event)
            et = event.get("type")
            if et == "init":
                print(f"[init] {event.get('message')} total={event.get('total_dtes', '?')}", flush=True)
            elif et == "progress":
                pd = event.get("processing_dte") or {}
                print(f"[progress] {event.get('current')}/{event.get('total')} id={pd.get('id')} rut={pd.get('rut')}", flush=True)
            elif et == "dte_result":
                print(
                    f"[result] dte_id={event.get('dte_id')} status={event.get('status')} "
                    f"msg={event.get('message')} wa={event.get('whatsapp_status')}",
                    flush=True,
                )
                if pd_rut := event.get("rut"):
                    pass
            elif et == "complete":
                print(
                    f"[complete] ok={event.get('successful_sends')} fail={event.get('failed_sends')} "
                    f"{event.get('message')}",
                    flush=True,
                )
            elif et == "error":
                print(f"[error] {event.get('message')}", flush=True)

        # Filtrar eventos del RUT objetivo
        target = [e for e in events if e.get("type") == "dte_result"]
        print("\n--- JSON resumen ---")
        print(json.dumps({"branch": BRANCH_ID, "type": DTE_TYPE, "target_rut": TARGET_RUT, "results": target}, indent=2, ensure_ascii=False))
    finally:
        db.close()


if __name__ == "__main__":
    main()
