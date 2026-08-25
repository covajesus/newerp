"""Notificaciones Slack para errores IntraJIS (canal intrajis_errors)."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Optional


DEFAULT_CHANNEL = "intrajis_errors"


def _webhook_url() -> str:
    return (
        (os.getenv("SLACK_ERRORS_WEBHOOK_URL") or "").strip()
        or (os.getenv("SLACK_WEBHOOK_URL") or "").strip()
    )


def _bot_token() -> str:
    return (os.getenv("SLACK_BOT_TOKEN") or "").strip()


def _channel() -> str:
    raw = (os.getenv("SLACK_ERRORS_CHANNEL") or DEFAULT_CHANNEL).strip()
    if raw and not raw.startswith("#") and not raw.startswith("C"):
        return f"#{raw}"
    return raw or f"#{DEFAULT_CHANNEL}"


def _enabled() -> bool:
    flag = (os.getenv("SLACK_ERRORS_ENABLED") or "1").strip().lower()
    if flag in ("0", "false", "no", "off"):
        return False
    return bool(_webhook_url() or _bot_token())


def _truncate(text: str, limit: int = 2500) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 20] + "\n…(truncado)"


def build_error_payload(
    *,
    process_name: str,
    process_code: str,
    message: str,
    log_id: Optional[int] = None,
    level: str = "error",
    log_datetime: Optional[str] = None,
    reference_type: Optional[str] = None,
    reference_id: Optional[int] = None,
    user_rut: Optional[str] = None,
    error_code: Optional[str] = None,
    detail: Optional[str] = None,
) -> dict[str, Any]:
    title = f":rotating_light: IntraJIS · {process_name or process_code}"
    lines = [
        f"*Proceso:* {process_name or '-'} (`{process_code}`)",
        f"*Nivel:* `{level}`",
        f"*Mensaje:* {_truncate(message, 800)}",
    ]
    if log_id is not None:
        lines.append(f"*Log ID:* `{log_id}`")
    if log_datetime:
        lines.append(f"*Fecha/hora:* `{log_datetime}`")
    if error_code:
        lines.append(f"*Código:* `{error_code}`")
    if user_rut:
        lines.append(f"*Usuario:* `{user_rut}`")
    if reference_type or reference_id is not None:
        lines.append(f"*Referencia:* `{reference_type or '-'}#{reference_id}`")
    if detail:
        lines.append(f"*Detalle:*\n```{_truncate(detail, 1200)}```")

    text = "\n".join(lines)
    return {
        "channel": _channel(),
        "username": "IntraJIS Errors",
        "icon_emoji": ":warning:",
        "text": title,
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": title[:140], "emoji": True},
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": text}},
        ],
    }


def _post_json(url: str, payload: dict[str, Any], headers: Optional[dict] = None) -> None:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8", **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        resp.read()


def send_error_to_slack(
    *,
    process_name: str,
    process_code: str,
    message: str,
    log_id: Optional[int] = None,
    level: str = "error",
    log_datetime: Optional[str] = None,
    reference_type: Optional[str] = None,
    reference_id: Optional[int] = None,
    user_rut: Optional[str] = None,
    error_code: Optional[str] = None,
    detail: Optional[str] = None,
) -> dict[str, Any]:
    """
    Envía el error al canal Slack intrajis_errors.
    Config:
      - SLACK_ERRORS_WEBHOOK_URL (recomendado: Incoming Webhook del canal)
      - o SLACK_BOT_TOKEN (+ SLACK_ERRORS_CHANNEL=intrajis_errors)
      - SLACK_ERRORS_ENABLED=0 para desactivar
    """
    if (level or "error").lower() != "error":
        return {"status": "skipped", "reason": "not_error_level"}
    if not _enabled():
        return {
            "status": "skipped",
            "reason": "slack_not_configured",
            "hint": "Defina SLACK_ERRORS_WEBHOOK_URL o SLACK_BOT_TOKEN en .env",
        }

    payload = build_error_payload(
        process_name=process_name,
        process_code=process_code,
        message=message,
        log_id=log_id,
        level=level,
        log_datetime=log_datetime,
        reference_type=reference_type,
        reference_id=reference_id,
        user_rut=user_rut,
        error_code=error_code,
        detail=detail,
    )

    try:
        webhook = _webhook_url()
        if webhook:
            # Incoming webhook: el canal suele estar fijado al crear el webhook
            _post_json(webhook, payload)
            return {"status": "success", "via": "webhook", "channel": _channel()}

        token = _bot_token()
        _post_json(
            "https://slack.com/api/chat.postMessage",
            {
                "channel": _channel(),
                "text": payload["text"],
                "blocks": payload["blocks"],
                "username": payload.get("username"),
                "icon_emoji": payload.get("icon_emoji"),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        return {"status": "success", "via": "bot", "channel": _channel()}
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="ignore")
        print(f"Slack notify HTTPError: {e.code} {err}")
        return {"status": "error", "message": f"HTTP {e.code}: {err}"}
    except Exception as e:
        print(f"Slack notify failed: {e}")
        return {"status": "error", "message": str(e)}
