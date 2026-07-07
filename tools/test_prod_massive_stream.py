"""Consume send_massive_dtes_stream en producción (misma URL que intrajis.com/send_dtes)."""
from __future__ import annotations

import json
import sys

import requests

BASE = "https://intrajisbackend.com/api/dtes/send_massive_dtes_stream"
BRANCH = int(sys.argv[1]) if len(sys.argv) > 1 else 16
DTE_TYPE = int(sys.argv[2]) if len(sys.argv) > 2 else 39
TARGET_RUT = sys.argv[3] if len(sys.argv) > 3 else "27141399-8"
TARGET_DTE_ID = int(sys.argv[4]) if len(sys.argv) > 4 else 11804034

url = f"{BASE}/{BRANCH}/{DTE_TYPE}"
print(f"GET {url}", flush=True)

target_events = []
with requests.get(url, stream=True, timeout=300) as resp:
    resp.raise_for_status()
    buf = ""
    for chunk in resp.iter_content(decode_unicode=True):
        if not chunk:
            continue
        buf += chunk
        while "\n\n" in buf:
            block, buf = buf.split("\n\n", 1)
            for line in block.splitlines():
                if not line.startswith("data: "):
                    continue
                data = json.loads(line[6:])
                et = data.get("type")
                if et == "init":
                    print(f"[init] {data.get('message')}", flush=True)
                elif et == "progress":
                    pd = data.get("processing_dte") or {}
                    if pd.get("rut") == TARGET_RUT or pd.get("id") == TARGET_DTE_ID:
                        print(
                            f"[progress] {data.get('current')}/{data.get('total')} "
                            f"id={pd.get('id')} rut={pd.get('rut')}",
                            flush=True,
                        )
                elif et == "dte_result":
                    if data.get("dte_id") == TARGET_DTE_ID:
                        target_events.append(data)
                        print(
                            f"[result] dte_id={data.get('dte_id')} status={data.get('status')} "
                            f"msg={data.get('message')}",
                            flush=True,
                        )
                        wa = data.get("whatsapp_response") or {}
                        print(
                            f"  WA status={wa.get('status')} accepted={wa.get('whatsapp_accepted')}",
                            flush=True,
                        )
                elif et == "complete":
                    print(
                        f"[complete] ok={data.get('successful_sends')} fail={data.get('failed_sends')} "
                        f"{data.get('message')}",
                        flush=True,
                    )

print("\n--- TARGET ---")
print(json.dumps(target_events, indent=2, ensure_ascii=False, default=str))
