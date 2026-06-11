"""Read PAYMENTS_* environment variables."""

from __future__ import annotations

import os


def payments_env(name: str, legacy_name: str | None = None, default: str = "") -> str:
    value = os.getenv(name)
    if value not in (None, ""):
        return value
    if legacy_name:
        legacy = os.getenv(legacy_name)
        if legacy not in (None, ""):
            return legacy
    return default
