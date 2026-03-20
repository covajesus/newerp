"""
Bot de WhatsApp (Meta Cloud API) para administradores: RUT → menú → venta del día por sucursal.
Envío de mensajes vía WhatsappClass (mismo token Graph que DTEs). Estado en memoria.
"""
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import pytz

_TZ_CL = pytz.timezone("America/Santiago")
# Tras login con RUT, no volver a pedirlo hasta pasar este tiempo
_SESSION_MAX = timedelta(days=1)
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.backend.classes.whatsapp_class import WhatsappClass
from app.backend.classes.cashier_sync_command_class import create_sync_commands, get_syncable_cashiers
from app.backend.db.models import BranchOfficeModel, CollectionModel, UserModel

# phone (wa_id) -> estado de conversación
_conversations: Dict[str, Dict[str, Any]] = {}

_MENU = (
    "*Marque la opción:*\n"
    "1️⃣ Conocer la venta del día\n"
    "2️⃣ Refrescar ventas (sincronizar cajas vía API)\n\n"
    "Responda con el *número*."
)


def _session_valid(state: dict) -> bool:
    """Sesión válida si hay authenticated_at y no pasó 1 día desde el login."""
    ts = state.get("authenticated_at")
    if ts is None:
        return False
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)
    now = datetime.now(_TZ_CL)
    if ts.tzinfo is None:
        ts = _TZ_CL.localize(ts)
    return (now - ts) < _SESSION_MAX


def _expire_session_if_needed(wa_id: str) -> None:
    """Si el login tiene más de 1 día, borrar sesión para pedir RUT de nuevo."""
    st = _conversations.get(wa_id)
    if not st:
        return
    if st.get("authenticated_at") and not _session_valid(st):
        _conversations.pop(wa_id, None)


def _normalize_rut_input(text: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Devuelve (rut_numérico_sin_dv, texto_original_limpio) para comparar con users.rut (Integer).
    Acepta 12345678-9, 12.345.678-9, 12345678, etc.
    """
    if not text:
        return None, None
    s = text.strip().upper().replace(".", "").replace(" ", "")
    m = re.match(r"^(\d{1,8})(?:-([0-9K]))?$", s)
    if not m:
        return None, None
    try:
        num = int(m.group(1))
        return num, s
    except ValueError:
        return None, None


def _find_admin_user(db: Session, rut_number: int) -> Optional[UserModel]:
    return (
        db.query(UserModel)
        .filter(UserModel.rut == rut_number, UserModel.rol_id.in_([1, 2]))
        .first()
    )


def _find_branch_by_name(db: Session, name: str) -> Optional[BranchOfficeModel]:
    if not name or len(name.strip()) < 2:
        return None
    q = name.strip()
    # Coincidencia parcial, insensible a mayúsculas
    return (
        db.query(BranchOfficeModel)
        .filter(BranchOfficeModel.branch_office.ilike(f"%{q}%"))
        .first()
    )


def _daily_sales_for_branch(db: Session, branch_office_id: int) -> Dict[str, Any]:
    tz = pytz.timezone("America/Santiago")
    today = datetime.now(tz).date()

    row = (
        db.query(
            func.coalesce(func.sum(CollectionModel.cash_gross_amount), 0),
            func.coalesce(func.sum(CollectionModel.card_gross_amount), 0),
            func.coalesce(func.sum(CollectionModel.total_tickets), 0),
        )
        .filter(
            CollectionModel.branch_office_id == branch_office_id,
            CollectionModel.added_date == today,
        )
        .first()
    )
    cash, card, tickets = row if row else (0, 0, 0)
    total_estimado = int(cash or 0) + int(card or 0)
    return {
        "fecha": today.strftime("%d/%m/%Y"),
        "efectivo_bruto": int(cash or 0),
        "tarjeta_bruto": int(card or 0),
        "total_aprox": total_estimado,
        "tickets": int(tickets or 0),
    }


def _send_text(db: Session, wa_id: str, body: str) -> None:
    WhatsappClass(db).send_text_message(wa_id, body)


def process_incoming_text(db: Session, wa_id: str, text: str) -> None:
    """
    Procesa un mensaje de texto entrante (número WhatsApp sin + en wa_id).
    """
    _expire_session_if_needed(wa_id)
    text = (text or "").strip()
    state = _conversations.get(wa_id, {})

    step = state.get("step", "waiting_rut")

    if step == "ask_rut":
        _send_text(
            db,
            wa_id,
            "👋 Bienvenido. Para continuar ingrese su *RUT* (ejemplo: 12345678-9).",
        )
        _conversations[wa_id] = {"step": "waiting_rut"}
        return

    if step == "waiting_rut":
        rut_num, _ = _normalize_rut_input(text)
        if rut_num is None:
            _send_text(
                db,
                wa_id,
                "❌ RUT no válido. Envíe solo números y guión, ej: *12345678-9*",
            )
            return

        user = _find_admin_user(db, rut_num)
        if not user:
            _send_text(
                db,
                wa_id,
                "⛔ No tiene permisos de administrador o el RUT no está registrado (solo roles 1 y 2).",
            )
            _conversations.pop(wa_id, None)
            return

        _conversations[wa_id] = {
            "step": "waiting_menu",
            "user_id": user.id,
            "rut": rut_num,
            "full_name": user.full_name or "",
            "authenticated_at": datetime.now(_TZ_CL),
        }
        _send_text(
            db,
            wa_id,
            f"✅ Hola {user.full_name or 'admin'}.\n\n{_MENU}",
        )
        return

    if step == "waiting_menu":
        low = text.strip().lower()
        if low in ("hola", "menu", "menú", "opciones", "inicio"):
            _send_text(db, wa_id, _MENU)
            return
        if text.strip() == "1":
            _conversations[wa_id]["step"] = "waiting_branch"
            _send_text(
                db,
                wa_id,
                "📍 Escriba el *nombre de la sucursal* (puede ser parte del nombre).",
            )
        elif text.strip() == "2":
            _conversations[wa_id]["step"] = "waiting_sync_branch"
            _send_text(
                db,
                wa_id,
                "🔄 *Sincronizar cajas*\n\n"
                "📍 Escriba el *nombre de la sucursal* (puede ser parte del nombre).",
            )
        else:
            _send_text(
                db,
                wa_id,
                "Opción no válida. Responda *1* o *2*.\n\n" + _MENU,
            )
        return

    if step == "waiting_sync_branch":
        branch = _find_branch_by_name(db, text)
        if not branch:
            _send_text(
                db,
                wa_id,
                "❌ No se encontró sucursal. Intente de nuevo.",
            )
            return
        cashiers = get_syncable_cashiers(db, branch.id)
        if not cashiers:
            _send_text(
                db,
                wa_id,
                "❌ No hay cajas activas registradas para esa sucursal.",
            )
            return
        lines = [f"• ID *{c.id}* — {c.cashier or 'sin nombre'}" for c in cashiers]
        lista = "\n".join(lines[:40])
        if len(cashiers) > 40:
            lista += "\n…"
        auth_at = state.get("authenticated_at")
        _conversations[wa_id] = {
            "step": "waiting_sync_scope",
            "user_id": state.get("user_id"),
            "rut": state.get("rut"),
            "full_name": state.get("full_name") or "",
            "authenticated_at": auth_at,
            "sync_branch_id": branch.id,
            "sync_branch_name": branch.branch_office or "",
        }
        _send_text(
            db,
            wa_id,
            f"📂 *{branch.branch_office}*\n\nCajas disponibles:\n{lista}\n\n"
            "Escriba *TODAS* para sincronizar *todas* las cajas, "
            "o solo el *número de ID* de una caja.",
        )
        return

    if step == "waiting_sync_scope":
        branch_id = state.get("sync_branch_id")
        if not branch_id:
            _conversations[wa_id]["step"] = "waiting_menu"
            _send_text(db, wa_id, "Sesión incompleta. " + _MENU)
            return
        raw = text.strip().upper()
        scope_all = raw == "TODAS" or raw == "TODA"
        single_id: Optional[int] = None
        if not scope_all:
            try:
                single_id = int(text.strip())
            except ValueError:
                _send_text(
                    db,
                    wa_id,
                    "❌ Escriba *TODAS* o el *ID numérico* de la caja.",
                )
                return
        res = create_sync_commands(
            db,
            branch_office_id=branch_id,
            requester_wa_id=wa_id,
            scope_all=scope_all,
            single_cashier_id=single_id,
        )
        auth_at = state.get("authenticated_at")
        base_state = {
            "step": "waiting_menu",
            "user_id": state.get("user_id"),
            "rut": state.get("rut"),
            "full_name": state.get("full_name") or "",
            "authenticated_at": auth_at,
        }
        if not res.get("ok"):
            _send_text(db, wa_id, f"❌ {res.get('message', 'Error')}")
            _conversations[wa_id] = {**base_state, "step": "waiting_sync_scope"}
            return
        parts = []
        for _row_id, cid, cname in res.get("created", []):
            parts.append(f"✅ Orden enviada a caja *{cid}* ({cname or '—'})")
        msg = (
            "\n".join(parts)
            + f"\n\n_Lote {res.get('batch_id', '')[:8]}…_\n"
            "Las cajas deben consultar el API (pull). "
            "Cuando terminen, recibirá aviso por aquí.\n\n"
            + _MENU
        )
        _send_text(db, wa_id, msg)
        _conversations[wa_id] = base_state
        return

    if step == "waiting_branch":
        branch = _find_branch_by_name(db, text)
        if not branch:
            _send_text(
                db,
                wa_id,
                "❌ No se encontró una sucursal con ese nombre. Intente de nuevo.",
            )
            return

        sales = _daily_sales_for_branch(db, branch.id)
        msg = (
            f"📊 *Venta del día* — {branch.branch_office}\n"
            f"Fecha: {sales['fecha']}\n\n"
            f"• Efectivo (bruto): ${sales['efectivo_bruto']:,}\n"
            f"• Tarjeta (bruto): ${sales['tarjeta_bruto']:,}\n"
            f"• Total aprox. (efectivo+tarjeta): ${sales['total_aprox']:,}\n"
            f"• Tickets: {sales['tickets']}\n\n"
            "¿Desea buscar *otra sucursal*? Marque *1*.\n"
            "¿Sincronizar cajas? Marque *2*.\n"
            "(Sesión activa 24 h; *hola* = menú principal.)"
        )
        _send_text(db, wa_id, msg)
        auth_at = state.get("authenticated_at")
        _conversations[wa_id] = {
            "step": "waiting_after_sale",
            "user_id": state.get("user_id"),
            "rut": state.get("rut"),
            "full_name": state.get("full_name") or "",
            "authenticated_at": auth_at,
        }
        return

    if step == "waiting_after_sale":
        low = text.strip().lower()
        if low in ("hola", "menu", "menú", "opciones", "inicio"):
            _conversations[wa_id]["step"] = "waiting_menu"
            _send_text(db, wa_id, _MENU)
            return
        if text.strip() == "1":
            _conversations[wa_id]["step"] = "waiting_branch"
            _send_text(
                db,
                wa_id,
                "📍 Escriba el *nombre de la sucursal* que desea consultar.",
            )
            return
        if text.strip() == "2":
            _conversations[wa_id]["step"] = "waiting_sync_branch"
            _send_text(
                db,
                wa_id,
                "🔄 *Sincronizar cajas*\n\n"
                "📍 Escriba el *nombre de la sucursal* (puede ser parte del nombre).",
            )
            return
        _send_text(
            db,
            wa_id,
            "Para *otra sucursal* marque *1*, para *sincronizar cajas* *2*. "
            "Menú: escriba *hola*.",
        )
        return

    # Estado desconocido: reiniciar
    _conversations[wa_id] = {"step": "ask_rut"}
    process_incoming_text(db, wa_id, "")


def _iter_messages_from_payload(payload: dict):
    """
    Formato estándar: object + entry[].changes[].value.messages[]
    Algunas pruebas de Meta envían solo el fragmento con value.messages.
    """
    out = []
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            for msg in value.get("messages") or []:
                out.append(msg)
    if not out and isinstance(payload.get("value"), dict):
        for msg in payload["value"].get("messages") or []:
            out.append(msg)
    return out


def handle_webhook_payload(db: Session, payload: dict) -> None:
    """
    Recorre el payload estándar de Meta WhatsApp Cloud API (field messages, v25).
    """
    try:
        messages = _iter_messages_from_payload(payload)
        for msg in messages:
            msg_type = msg.get("type")
            if msg_type != "text":
                continue
            wa_id = msg.get("from")
            body = (msg.get("text") or {}).get("body") or ""
            if not wa_id:
                continue

            _expire_session_if_needed(wa_id)

            # Primera vez: si envía RUT directo, validar sin pedir dos pasos
            if wa_id not in _conversations:
                rut_num, _ = _normalize_rut_input(body.strip())
                if rut_num is not None:
                    _conversations[wa_id] = {"step": "waiting_rut"}
                    process_incoming_text(db, wa_id, body.strip())
                    continue
                _conversations[wa_id] = {"step": "ask_rut"}
                process_incoming_text(db, wa_id, "")
                continue

            process_incoming_text(db, wa_id, body)
    except Exception as e:
        print(f"[whatsapp_admin_bot] Error procesando webhook: {e}")
