"""Llama al cron de estados SII DTE emitidos (SimpleFactura).

Uso:
  python scripts/cron_dte_sii_status.py
  python scripts/cron_dte_sii_status.py --url https://intrajisbackend.com/api/dte_sii_status/cron
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

import requests

DEFAULT_URL = "https://intrajisbackend.com/api/dte_sii_status/cron"
# Sync con chunks + fallback diario puede superar 5 min.
TIMEOUT = 900


def main() -> int:
    parser = argparse.ArgumentParser(description="Cron sync estados SII DTE")
    parser.add_argument("--url", default=DEFAULT_URL)
    args = parser.parse_args()

    started = datetime.now().isoformat(sep=" ", timespec="seconds")
    print(f"[{started}] GET {args.url}")
    try:
        response = requests.get(args.url, timeout=TIMEOUT)
    except requests.RequestException as exc:
        print(f"ERROR de red: {exc}", file=sys.stderr)
        return 1

    print(f"HTTP {response.status_code}")
    try:
        body = response.json()
        print(json.dumps(body, ensure_ascii=False, indent=2)[:4000])
    except ValueError:
        print((response.text or "")[:2000])

    return 0 if response.status_code == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
