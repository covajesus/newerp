"""Mapeo de rutas API → proceso + helpers de logging global."""
from __future__ import annotations

import re
from typing import Optional

# Prefijos de ruta (sin /api) → código de proceso
ROUTE_PROCESS_MAP: list[tuple[str, str, str]] = [
    ("/customer_bills", "customer_bills", "Boletas - Facturas clientes"),
    ("/customer_tickets", "customer_tickets", "Boletas - Tickets clientes"),
    ("/customer_tickets_bills", "customer_tickets_bills", "Boletas - Tickets/Facturas"),
    ("/customer_credit_notes", "customer_credit_notes", "Notas de crédito"),
    ("/machine_tickets", "machine_tickets", "Boletas máquina"),
    ("/cashier_dtes", "cashier_dtes", "DTE cajeros"),
    ("/dtes", "dtes", "DTEs / documentos tributarios"),
    ("/received_tributary_documents", "received_tributary_docs", "Facturas recibidas"),
    ("/received_inbox", "received_inbox", "Bandeja recibidos SII"),
    ("/quotations", "quotations", "Track abonados / cotizaciones"),
    ("/bank_statements", "bank_statements", "Cartolas bancarias"),
    ("/honoraries", "honoraries", "Honorarios"),
    ("/payments", "payments", "Pagos / pasarela"),
    ("/folios", "folios", "Folios"),
    ("/cafs", "cafs", "CAF"),
    ("/customers", "customers", "Clientes"),
    ("/collections", "collections", "Recaudaciones"),
    ("/capitulations", "capitulations", "Capitulaciones"),
    ("/deposits", "deposits", "Depósitos"),
    ("/accounting_entries", "accounting_entries", "Asientos contables"),
    ("/accounting_accounts", "accounting_accounts", "Cuentas contables"),
    ("/movements", "movements", "Inventario - movimientos"),
    ("/products", "products", "Inventario - productos"),
    ("/users", "users", "Usuarios"),
    ("/employees", "employees", "Empleados"),
    ("/branch_offices", "branch_offices", "Sucursales"),
    ("/settings", "settings", "Configuraciones"),
    ("/authentications", "authentications", "Autenticación"),
    ("/whatsapp_webhook", "whatsapp", "WhatsApp"),
    ("/email", "email_send", "Email - Envío"),
]

CRUD_HINTS = (
    ("/store", "store", "crear"),
    ("/update", "update", "actualizar"),
    ("/delete", "delete", "eliminar"),
    ("/edit", "edit", "editar"),
    ("/generate", "generate", "generar"),
    ("/send", "send", "enviar"),
    ("/emit", "emit", "emitir"),
    ("/import", "import", "importar"),
    ("/export", "export", "exportar"),
)


def normalize_path(path: str) -> str:
    p = (path or "").strip()
    if p.startswith("/api"):
        p = p[4:] or "/"
    return p


def resolve_process_from_path(path: str) -> tuple[str, str]:
    """Devuelve (process_code, process_name) según la ruta."""
    p = normalize_path(path)
    for prefix, code, name in ROUTE_PROCESS_MAP:
        if p == prefix or p.startswith(prefix + "/") or p.startswith(prefix + "?"):
            return code, name
    # fallback: primer segmento
    parts = [x for x in p.split("/") if x]
    if parts:
        code = re.sub(r"[^a-z0-9_]+", "_", parts[0].lower())[:64] or "api"
        return code, f"API - {parts[0]}"
    return "api", "API - General"


def resolve_crud_action(path: str, method: str) -> Optional[str]:
    p = normalize_path(path).lower()
    for needle, action, _label in CRUD_HINTS:
        if needle in p:
            return action
    method = (method or "").upper()
    return {
        "POST": "create_or_action",
        "PUT": "update",
        "PATCH": "update",
        "DELETE": "delete",
        "GET": "read",
    }.get(method)


def build_seed_processes() -> list[tuple[str, str, str]]:
    """Procesos base + módulos de boletas/track/CRUD."""
    base = [
        ("api", "API - General", "Errores no mapeados a un módulo"),
        ("honorary_store", "Honorarios - Solicitar", "Creación / store de honorario"),
        ("honorary_generate", "Honorarios - Aceptar", "Aceptación / generate de honorario"),
        ("honorary_send_sii", "Honorarios - Emitir BTE SII", "Emisión BTE en SII"),
        ("honorary_resend_sii", "Honorarios - Reenviar BTE SII", "Reenvío BTE desde listado"),
        ("honorary_annul_bte", "Honorarios - Anular BTE SII", "Anulación de BTE en SII"),
        ("honorary_impute", "Honorarios - Imputar", "Imputación de honorario"),
        ("honorary_validate", "Honorarios - Validar RUT", "Validación de RUT / periodo"),
        ("honoraries", "Honorarios", "Módulo honorarios (CRUD / listados)"),
        ("email_send", "Email - Envío", "Envío de correos (SMTP / DTE / cotizaciones)"),
        ("email_dte_subscriber", "Email - DTE abonados", "Correos de DTE a abonados"),
    ]
    seen = {c for c, _, _ in base}
    for _prefix, code, name in ROUTE_PROCESS_MAP:
        if code not in seen:
            base.append((code, name, f"Errores del módulo {name}"))
            seen.add(code)
    return base
