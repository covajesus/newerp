"""
Catálogo unificado de procesos IntraJIS (backend API + frontend).
Cada prefijo de API y cada área de UI se mapea a processes.code / processes.name.
"""
from __future__ import annotations

import re
from typing import Optional

# (api_prefix, code, name)
BACKEND_ROUTE_PROCESS_MAP: list[tuple[str, str, str]] = [
    ("/about_us", "about_us", "Nosotros"),
    ("/account_types", "account_types", "Tipos de cuenta"),
    ("/accountability", "accountability", "Rendiciones / accountability"),
    ("/accounting_accounts", "accounting_accounts", "Cuentas contables"),
    ("/accounting_entries", "accounting_entries", "Asientos contables"),
    ("/alert_types", "alert_types", "Tipos de alerta"),
    ("/alerts", "alerts", "Alertas"),
    ("/authentications", "authentications", "Autenticación"),
    ("/bank_account_users", "bank_account_users", "Cuentas bancarias usuarios"),
    ("/bank_statements", "bank_statements", "Cartolas bancarias"),
    ("/banks", "banks", "Bancos"),
    ("/biller_data", "biller_data", "Datos facturador"),
    ("/blog", "blog", "Blog"),
    ("/branch_office_transbank", "branch_office_transbank", "Transbank sucursales"),
    ("/branch_offices", "branch_offices", "Sucursales"),
    ("/budgets", "budgets", "Presupuestos"),
    ("/cafs", "cafs", "CAF"),
    ("/capitulations", "capitulations", "Capitulaciones"),
    ("/carbon_monoxides", "carbon_monoxides", "Monóxido de carbono"),
    ("/cash_reserves", "cash_reserves", "Fondos de caja"),
    ("/cashier_dtes", "cashier_dtes", "DTE cajeros"),
    ("/cashier_sync", "cashier_sync", "Sincronización cajas"),
    ("/cashiers", "cashiers", "Cajeros"),
    ("/causals", "causals", "Causales"),
    ("/civil_states", "civil_states", "Estados civiles"),
    ("/clock_users", "clock_users", "Usuarios reloj"),
    ("/collections", "collections", "Recaudaciones"),
    ("/communes", "communes", "Comunas"),
    ("/complaints", "complaints", "Reclamos"),
    ("/contacts", "contacts", "Contactos"),
    ("/contract_data", "contract_data", "Datos de contrato"),
    ("/contract_types", "contract_types", "Tipos de contrato"),
    ("/contracts", "contracts", "Contratos"),
    ("/customer_bills", "customer_bills", "Boletas - Facturas clientes"),
    ("/customer_collections", "customer_collections", "Cobranza clientes"),
    ("/customer_credit_notes", "customer_credit_notes", "Notas de crédito"),
    ("/customer_tickets", "customer_tickets", "Boletas - Tickets clientes"),
    ("/customer_tickets_bills", "customer_tickets_bills", "Boletas - Tickets/Facturas"),
    ("/customers", "customers", "Clientes"),
    ("/delivery_address_tags", "delivery_address_tags", "Etiquetas de despacho"),
    ("/demarcations", "demarcations", "Demarcaciones"),
    ("/deposits", "deposits", "Depósitos"),
    ("/document_types", "document_types", "Tipos de documento"),
    ("/documents", "documents", "Documentos"),
    ("/dte_line_item_details", "dte_line_item_details", "Detalle ítems DTE"),
    ("/dte_line_item_names", "dte_line_item_names", "Nombres ítems DTE"),
    ("/dtes", "dtes", "DTEs / documentos tributarios"),
    ("/employee_contracts", "employee_contracts", "Contratos empleados"),
    ("/employee_extras", "employee_extras", "Extras empleados"),
    ("/employee_interships", "employee_interships", "Pasantías empleados"),
    ("/employee_labor_data", "employee_labor_data", "Datos laborales"),
    ("/employee_types", "employee_types", "Tipos de empleado"),
    ("/employees", "employees", "Empleados"),
    ("/end_documents", "end_documents", "Documentos de término"),
    ("/expense_types", "expense_types", "Tipos de gasto"),
    ("/family_core_data", "family_core_data", "Núcleo familiar"),
    ("/family_types", "family_types", "Tipos de familia"),
    ("/files", "files", "Archivos"),
    ("/folios", "folios", "Folios"),
    ("/frecuent_questions", "frecuent_questions", "Preguntas frecuentes"),
    ("/genders", "genders", "Géneros"),
    ("/group_details", "group_details", "Detalle de grupos"),
    ("/holidays", "holidays", "Feriados"),
    ("/honoraries", "honoraries", "Honorarios"),
    ("/honorary_reasons", "honorary_reasons", "Motivos de honorario"),
    ("/interships", "interships", "Pasantías"),
    ("/kardex_data", "kardex_data", "Kardex data"),
    ("/kardex_values", "kardex_values", "Kardex"),
    ("/kpis", "kpis", "KPIs"),
    ("/letter_types", "letter_types", "Tipos de carta"),
    ("/logo", "logo", "Logo"),
    ("/logs", "logs", "Logs del sistema"),
    ("/machine_tickets", "machine_tickets", "Boletas máquina"),
    ("/maintenances", "maintenances", "Mantenciones"),
    ("/medical_license_types", "medical_license_types", "Tipos licencia médica"),
    ("/mesh_data", "mesh_data", "Datos de malla"),
    ("/meshes", "meshes", "Mallas"),
    ("/months", "months", "Meses"),
    ("/movement_products", "movement_products", "Productos en movimientos"),
    ("/movements", "movements", "Inventario - movimientos"),
    ("/nationalities", "nationalities", "Nacionalidades"),
    ("/old_documents_employees", "old_documents_employees", "Documentos empleados (legacy)"),
    ("/old_employee_extras", "old_employee_extras", "Extras empleados (legacy)"),
    ("/old_employee_labor_data", "old_employee_labor_data", "Datos laborales (legacy)"),
    ("/old_employees", "old_employees", "Empleados (legacy)"),
    ("/old_family_core_data", "old_family_core_data", "Núcleo familiar (legacy)"),
    ("/old_medical_licenses", "old_medical_licenses", "Licencias médicas (legacy)"),
    ("/old_salary_settlements", "old_salary_settlements", "Liquidaciones (legacy)"),
    ("/old_vacations", "old_vacations", "Vacaciones (legacy)"),
    ("/patents", "patents", "Patentes"),
    ("/patology_types", "patology_types", "Tipos de patología"),
    ("/payments", "payments", "Pagos / pasarela"),
    ("/payroll_afp_quotes", "payroll_afp_quotes", "Remuneraciones - AFP"),
    ("/payroll_calculations", "payroll_calculations", "Remuneraciones - cálculos"),
    ("/payroll_employees", "payroll_employees", "Remuneraciones - empleados"),
    ("/payroll_family_burdens", "payroll_family_burdens", "Remuneraciones - cargas"),
    ("/payroll_indicators", "payroll_indicators", "Remuneraciones - indicadores"),
    ("/payroll_item_values", "payroll_item_values", "Remuneraciones - valores ítem"),
    ("/payroll_items", "payroll_items", "Remuneraciones - ítems"),
    ("/payroll_manual_inputs", "payroll_manual_inputs", "Remuneraciones - inputs manuales"),
    ("/payroll_openings", "payroll_openings", "Remuneraciones - aperturas"),
    ("/payroll_periods", "payroll_periods", "Remuneraciones - periodos"),
    ("/payroll_second_category_taxes", "payroll_second_category_taxes", "Remuneraciones - 2da categoría"),
    ("/payroll_umployment_insurances", "payroll_umployment_insurances", "Remuneraciones - cesantía"),
    ("/payrolls", "payrolls", "Remuneraciones / payrolls"),
    ("/pentions", "pentions", "Pensiones"),
    ("/possible_employees", "possible_employees", "Posibles empleados"),
    ("/preventive_maintenances", "preventive_maintenances", "Mantención preventiva"),
    ("/previred_indicators", "previred_indicators", "Indicadores Previred"),
    ("/principals", "principals", "Principales"),
    ("/product_categories", "product_categories", "Categorías de producto"),
    ("/products", "products", "Inventario - productos"),
    ("/progressive_vacations", "progressive_vacations", "Vacaciones progresivas"),
    ("/provisional_indicators", "provisional_indicators", "Indicadores provisionales"),
    ("/quotations", "quotations", "Track abonados / cotizaciones"),
    ("/received_inbox", "received_inbox", "Bandeja recibidos SII"),
    ("/received_tributary_documents", "received_tributary_docs", "Facturas recibidas"),
    ("/redcomercio_data", "redcomercio_data", "Redcomercio"),
    ("/reference_types", "reference_types", "Tipos de referencia"),
    ("/regimes", "regimes", "Regímenes"),
    ("/regions", "regions", "Regiones"),
    ("/remunerations", "remunerations", "Remuneraciones"),
    ("/rols", "rols", "Roles"),
    ("/schedule", "schedule", "Horarios"),
    ("/scrappers", "scrappers", "Scrapers"),
    ("/seats", "seats", "Asientos / seats"),
    ("/secondary_category_taxes", "secondary_category_taxes", "Impuesto 2da categoría"),
    ("/segments", "segments", "Segmentos"),
    ("/settings", "settings", "Configuraciones"),
    ("/sinister_types", "sinister_types", "Tipos de siniestro"),
    ("/sinisters", "sinisters", "Siniestros"),
    ("/slider", "slider", "Slider"),
    ("/social_laws", "social_laws", "Leyes sociales"),
    ("/summary-indicators", "summary_indicators", "Indicadores resumen"),
    ("/supervisors", "supervisors", "Supervisores"),
    ("/suppliers", "suppliers", "Proveedores"),
    ("/surveys", "surveys", "Encuestas"),
    ("/taxes", "taxes", "Impuestos / patentes municipales"),
    ("/transbank_statements", "transbank_statements", "Cartolas Transbank"),
    ("/turns", "turns", "Turnos"),
    ("/uniform_types", "uniform_types", "Tipos de uniforme"),
    ("/uniforms", "uniforms", "Uniformes"),
    ("/users", "users", "Usuarios"),
    ("/vacations", "vacations", "Vacaciones"),
    ("/whatsapp", "whatsapp", "WhatsApp"),
    ("/zones", "zones", "Zonas"),
]

# Procesos especiales (no son solo un router genérico)
SPECIAL_PROCESSES: list[tuple[str, str, str]] = [
    ("api", "API - General", "Errores no mapeados a un módulo"),
    ("frontend", "Frontend - General", "Errores de UI / consola no mapeados"),
    ("frontend_console", "Frontend - Console", "console.error / errores de consola"),
    ("frontend_runtime", "Frontend - Runtime", "window.onerror / excepciones UI"),
    ("frontend_promise", "Frontend - Promise", "unhandledrejection"),
    ("frontend_vue", "Frontend - Vue", "Vue errorHandler"),
    ("frontend_axios", "Frontend - Axios", "Errores HTTP axios desde el cliente"),
    ("honorary_store", "Honorarios - Solicitar", "Creación / store de honorario"),
    ("honorary_generate", "Honorarios - Aceptar", "Aceptación / generate de honorario"),
    ("honorary_send_sii", "Honorarios - Emitir BTE SII", "Emisión BTE en SII"),
    ("honorary_resend_sii", "Honorarios - Reenviar BTE SII", "Reenvío BTE desde listado"),
    ("honorary_annul_bte", "Honorarios - Anular BTE SII", "Anulación de BTE en SII"),
    ("honorary_impute", "Honorarios - Imputar", "Imputación de honorario"),
    ("honorary_validate", "Honorarios - Validar RUT", "Validación de RUT / periodo"),
    ("honorary_massive_accountability", "Honorarios - Imputación masiva", "Errores de imputación masiva de honorarios"),
    ("received_dte_massive_accountability", "Facturas recibidas - Imputación masiva", "Errores de imputación masiva DTE recibidos"),
    ("received_credit_note_massive_accountability", "NC recibidas - Imputación masiva", "Errores de imputación masiva NC recibidas"),
    ("email_send", "Email - Envío", "Envío de correos (SMTP / DTE / cotizaciones)"),
    ("email_dte_subscriber", "Email - DTE abonados", "Correos de DTE a abonados"),
    ("dte_massive_whatsapp", "DTE - Envío masivo WhatsApp", "Reenvío / envío masivo WhatsApp"),
    ("user_audit", "Auditoría de usuarios", "Registro de actividad UI/API por usuario"),
]

# Rutas frontend (path starts with) → proceso
FRONTEND_PATH_PROCESS_MAP: list[tuple[str, str, str]] = [
    ("/honoraries", "honoraries", "Honorarios"),
    ("/honorary", "honoraries", "Honorarios"),
    ("/customer_tickets_v2", "customer_tickets", "Boletas - Tickets clientes v2"),
    ("/customer_tickets", "customer_tickets", "Boletas - Tickets clientes"),
    ("/customer_ticket_v2", "customer_tickets", "Boletas - Tickets clientes v2"),
    ("/customer_ticket_bill", "customer_tickets_bills", "Boletas - Tickets/Facturas"),
    ("/customer_ticket", "customer_tickets", "Boletas - Tickets clientes"),
    ("/customer_bills_v2", "customer_bills", "Boletas - Facturas clientes v2"),
    ("/customer_bills", "customer_bills", "Boletas - Facturas clientes"),
    ("/customer_bill_v2", "customer_bills", "Boletas - Facturas clientes v2"),
    ("/customer_bill", "customer_bills", "Boletas - Facturas clientes"),
    ("/created_subscriber_tickets_bills", "customer_tickets_bills", "Tickets/Facturas creados"),
    ("/created_subscriber_tickets", "customer_tickets", "Tickets abonados creados"),
    ("/created_subscriber_bills", "customer_bills", "Facturas abonados creadas"),
    ("/created_subscriber", "quotations", "Track abonados"),
    ("/created_machine_tickets", "machine_tickets", "Boletas máquina creadas"),
    ("/created_machine", "machine_tickets", "Boletas máquina"),
    ("/open_customer_billing_period", "customer_tickets", "Apertura periodo facturación"),
    ("/subscriber_payment_history", "quotations", "Historial pagos abonado"),
    ("/subscriber_assets", "accountability", "Activos abonados"),
    ("/quotations", "quotations", "Track abonados / cotizaciones"),
    ("/quotation", "quotations", "Track abonados / cotizaciones"),
    ("/credit_notes", "customer_credit_notes", "Notas de crédito"),
    ("/machine_ticket", "machine_tickets", "Boletas máquina"),
    ("/caf_machine_tickets", "cafs", "CAF máquina"),
    ("/caf_machine_ticket", "cafs", "CAF máquina"),
    ("/caf_machine", "cafs", "CAF"),
    ("/pre_caf_machine_tickets", "cafs", "Pre-CAF máquina"),
    ("/received_inbox", "received_inbox", "Bandeja recibidos SII"),
    ("/received_tributary_documents", "received_tributary_docs", "Facturas recibidas"),
    ("/received_tributary", "received_tributary_docs", "Facturas recibidas"),
    ("/pay_received_tributary_documents", "received_tributary_docs", "Pago facturas recibidas"),
    ("/pay_received_tributary_document", "received_tributary_docs", "Pago facturas recibidas"),
    ("/pay_received_tributary", "received_tributary_docs", "Pago facturas recibidas"),
    ("/tributary_document", "received_tributary_docs", "Facturas recibidas"),
    ("/review_dte_payments", "received_tributary_docs", "Revisión pagos DTE"),
    ("/collections/refresh", "collections", "Refresco recaudaciones"),
    ("/collection_details", "collections", "Detalle recaudaciones"),
    ("/collections", "collections", "Recaudaciones"),
    ("/collection", "collections", "Recaudaciones"),
    ("/deposits", "deposits", "Depósitos"),
    ("/deposit", "deposits", "Depósitos"),
    ("/total_accepted_capitulations", "capitulations", "Capitulaciones aceptadas"),
    ("/pay-capitulation-details", "capitulations", "Pago capitulaciones detalle"),
    ("/pay-capitulations", "capitulations", "Pago capitulaciones"),
    ("/capitulations", "capitulations", "Capitulaciones"),
    ("/capitulation", "capitulations", "Capitulaciones"),
    ("/bank_statement_deposit", "bank_statements", "Cartola depósito"),
    ("/bank_statement_dte", "bank_statements", "Cartola DTE"),
    ("/bank_statement", "bank_statements", "Cartolas bancarias"),
    ("/bank_statements", "bank_statements", "Cartolas bancarias"),
    ("/customer_bank_statements", "bank_statements", "Cartolas bancarias"),
    ("/deposit_bank_statements", "bank_statements", "Cartolas bancarias"),
    ("/transbank_statements", "transbank_statements", "Cartolas Transbank"),
    ("/transbank_statement", "transbank_statements", "Cartolas Transbank"),
    ("/transbank_data", "branch_office_transbank", "Datos Transbank"),
    ("/transbank", "transbank_statements", "Cartolas Transbank"),
    ("/contracts", "contracts", "Contratos"),
    ("/contract", "contracts", "Contratos"),
    ("/taxes", "taxes", "Impuestos"),
    ("/tax", "taxes", "Impuestos"),
    ("/patents", "patents", "Patentes"),
    ("/patent", "patents", "Patentes"),
    ("/sinisters", "sinisters", "Siniestros"),
    ("/sinister", "sinisters", "Siniestros"),
    ("/simple_sinister", "sinisters", "Siniestros"),
    ("/customer_collections", "customer_collections", "Cobranza clientes"),
    ("/customers", "customers", "Clientes"),
    ("/customer", "customers", "Clientes"),
    ("/users", "users", "Usuarios"),
    ("/user", "users", "Usuarios"),
    ("/surveys", "surveys", "Encuestas"),
    ("/survey", "surveys", "Encuestas"),
    ("/inventory/kardex", "kardex_values", "Kardex"),
    ("/inventory/movements", "movements", "Inventario - movimientos"),
    ("/inventory/products", "products", "Inventario - productos"),
    ("/inventory", "products", "Inventario"),
    ("/products", "products", "Inventario - productos"),
    ("/movements", "movements", "Inventario - movimientos"),
    ("/kardex", "kardex_values", "Kardex"),
    ("/accounting_accounts", "accounting_accounts", "Cuentas contables"),
    ("/accounting_entries", "accounting_entries", "Asientos contables"),
    ("/accounting-entries", "accounting_entries", "Asientos contables"),
    ("/accounting", "accounting_entries", "Contabilidad"),
    ("/manual_asset", "accountability", "Activo manual"),
    ("/massive_accountability", "accountability", "Rendición masiva"),
    ("/assets", "accountability", "Activos / accountability"),
    ("/remuneration", "remunerations", "Remuneraciones"),
    ("/management/labels", "delivery_address_tags", "Etiquetas despacho"),
    ("/management/cashier_tickets", "cashier_dtes", "Tickets cajero"),
    ("/management", "capitulations", "Gestión / management"),
    ("/reimbursements", "capitulations", "Reembolsos"),
    ("/cash_reserves", "cash_reserves", "Fondos de caja"),
    ("/cash_reserve", "cash_reserves", "Fondos de caja"),
    ("/employees_interships", "employee_interships", "Pasantías empleados"),
    ("/employee_intership", "employee_interships", "Pasantías empleados"),
    ("/interships", "interships", "Pasantías"),
    ("/intership", "interships", "Pasantías"),
    ("/carbon_monoxides", "carbon_monoxides", "Monóxido de carbono"),
    ("/carbon_monoxide", "carbon_monoxides", "Monóxido de carbono"),
    ("/maintenances", "maintenances", "Mantenciones"),
    ("/maintenance/preventive", "preventive_maintenances", "Mantención preventiva"),
    ("/maintenance", "maintenances", "Mantenciones"),
    ("/preventive", "preventive_maintenances", "Mantención preventiva"),
    ("/demarcations", "demarcations", "Demarcaciones"),
    ("/demarcation", "demarcations", "Demarcaciones"),
    ("/branch_offices", "branch_offices", "Sucursales"),
    ("/branch_office", "branch_offices", "Sucursales"),
    ("/expense_types", "expense_types", "Tipos de gasto"),
    ("/expense_type", "expense_types", "Tipos de gasto"),
    ("/group_details", "group_details", "Detalle de grupos"),
    ("/group_detail", "group_details", "Detalle de grupos"),
    ("/dte_line_item_names", "dte_line_item_names", "Nombres ítems DTE"),
    ("/dte_line_item_name", "dte_line_item_names", "Nombres ítems DTE"),
    ("/dte_line_item_details", "dte_line_item_details", "Detalle ítems DTE"),
    ("/dte_line_item_detail", "dte_line_item_details", "Detalle ítems DTE"),
    ("/tags", "delivery_address_tags", "Etiquetas"),
    ("/user_audits", "user_audit", "Auditoría de usuarios"),
    ("/folios/segment", "folios", "Segmentos de folios"),
    ("/folios/report", "folios", "Reporte folios"),
    ("/folios/request", "folios", "Solicitud folios"),
    ("/folios", "folios", "Folios"),
    ("/folio_quantity", "folios", "Cantidad folios"),
    ("/folio", "folios", "Folios"),
    ("/cashiers", "cashiers", "Cajeros"),
    ("/cashier", "cashiers", "Cajeros"),
    ("/latest_update_cashier", "cashier_sync", "Última sync cajero"),
    ("/bank_account_user", "bank_account_users", "Cuentas bancarias usuarios"),
    ("/whatsapp", "whatsapp", "WhatsApp"),
    ("/dte/import_by_rut", "dtes", "Importar DTE por RUT"),
    ("/dte/resend", "dtes", "Reenvío DTE"),
    ("/send_dtes", "dtes", "Envío DTEs"),
    ("/settings", "settings", "Configuraciones"),
    ("/payments", "payments", "Pagos"),
    ("/payment", "payments", "Pagos"),
    ("/login", "authentications", "Autenticación"),
    ("/", "frontend", "Frontend - General"),
]

# Alias usado por el middleware HTTP
ROUTE_PROCESS_MAP = BACKEND_ROUTE_PROCESS_MAP

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
    ("/massive", "massive", "masivo"),
)


def normalize_path(path: str) -> str:
    p = (path or "").strip()
    if p.startswith("/api"):
        p = p[4:] or "/"
    # quitar query
    if "?" in p:
        p = p.split("?", 1)[0]
    return p or "/"


def resolve_process_from_path(path: str) -> tuple[str, str]:
    """Devuelve (process_code, process_name) según la ruta API."""
    p = normalize_path(path)
    # Ordenar por prefijo más largo primero
    for prefix, code, name in sorted(BACKEND_ROUTE_PROCESS_MAP, key=lambda x: len(x[0]), reverse=True):
        if p == prefix or p.startswith(prefix + "/") or p.startswith(prefix + "?"):
            return code, name
    parts = [x for x in p.split("/") if x]
    if parts:
        code = re.sub(r"[^a-z0-9_]+", "_", parts[0].lower())[:64] or "api"
        return code, f"API - {parts[0]}"
    return "api", "API - General"


def resolve_process_from_frontend_path(path: str) -> tuple[str, str]:
    """Devuelve (process_code, process_name) según la ruta del SPA."""
    p = normalize_path(path)
    if not p.startswith("/"):
        p = "/" + p
    for prefix, code, name in sorted(FRONTEND_PATH_PROCESS_MAP, key=lambda x: len(x[0]), reverse=True):
        if prefix == "/":
            continue
        if p == prefix or p.startswith(prefix + "/") or p.startswith(prefix + "?"):
            return code, name
    return "frontend", "Frontend - General"


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
    """Une especialidades + todos los módulos backend + frontend."""
    base: list[tuple[str, str, str]] = []
    seen: set[str] = set()

    def add(code: str, name: str, description: str) -> None:
        if code in seen:
            return
        base.append((code, name, description))
        seen.add(code)

    for code, name, description in SPECIAL_PROCESSES:
        add(code, name, description)

    for _prefix, code, name in BACKEND_ROUTE_PROCESS_MAP:
        add(code, name, f"Backend API {_prefix}")

    for _prefix, code, name in FRONTEND_PATH_PROCESS_MAP:
        add(code, name, f"Frontend UI {_prefix}")

    return base
