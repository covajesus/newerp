r"""
Agente pull para instalar en cada PC-caja (Windows: tarea al inicio o NSSM).

Tu script actual (el que corre cada 1 h) lee `stored_tickets` y hace POST a
`intranet_url_to_collect_data`. No hay que cambiar esa lógica: el agente solo
**vuelve a ejecutar el mismo .py** cuando WhatsApp (opción 2) deja un comando en el servidor.

Endpoints del ERP (producción por defecto: intrajisbackend.com):
  GET  https://intrajisbackend.com/api/cashier_sync/{CAJA_ID}/next
  POST https://intrajisbackend.com/api/cashier_sync/{CAJA_ID}/commands/{id}/complete

Ejemplo de variables en Windows (CMD), asumiendo tu envío está en C:\caja\enviar_recaudacion.py
y ahí mismo tienes sql.py (para que import sql funcione):

  set CAJA_ID=12
  set CAJA_SYNC_API_BASE=https://intrajisbackend.com/api
  set CAJA_SUBIR_VENTAS_CMD=python C:\caja\enviar_recaudacion.py
  set CAJA_SUBIR_VENTAS_CWD=C:\caja
  set CAJA_SYNC_API_TOKEN=el_mismo_que_CASHIER_SYNC_API_TOKEN_en_el_servidor
  python C:\caja\caja_pull_sync_agent.py

Si usas venv, usa la ruta completa a python.exe en CAJA_SUBIR_VENTAS_CMD.

La tarea programada cada 1 h puede seguir igual (respaldo). Este proceso = on-demand.

Dependencias en la caja: pip install requests
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from typing import Any

import requests

# ============ CONFIGURA EN CADA CAJA ============
# URL pública del ERP (backend intranet)
BASE_URL = os.getenv("CAJA_SYNC_API_BASE", "https://intrajisbackend.com/api").rstrip("/")
# ID numérico de esta caja en el ERP (el que ves en WhatsApp al listar cajas)
CAJA_ID = int(os.getenv("CAJA_ID", "0"))
# Mismo valor que CASHIER_SYNC_API_TOKEN en el servidor (.env). Vacío si no usas token.
TOKEN = os.getenv("CASHIER_SYNC_API_TOKEN", "").strip()
# Cada cuántos segundos preguntar al servidor
POLL_SECONDS = float(os.getenv("CAJA_SYNC_POLL_SECONDS", "10"))
# Comando que sube las ventas = el MISMO que ya programaste cada 1 h (envío recaudación)
SUBIR_VENTAS = os.getenv(
    "CAJA_SUBIR_VENTAS_CMD",
    # ejemplo: r'python C:\caja\enviar_recaudacion.py'
    "",
)
# Carpeta de trabajo (necesaria si tu script hace "import sql" y sql.py está ahí)
SUBIR_VENTAS_CWD = os.getenv("CAJA_SUBIR_VENTAS_CWD", "").strip() or None


def _headers() -> dict[str, str]:
    h: dict[str, str] = {}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    return h


def ejecutar_subida_ventas() -> tuple[int, str]:
    """
    Ejecuta tu proceso actual de subida. Devuelve (código_salida, salida_texto).
    Si SUBIR_VENTAS está vacío, solo simula éxito (para pruebas).
    """
    if not SUBIR_VENTAS.strip():
        return 0, "CAJA_SUBIR_VENTAS_CMD no configurado (simulado OK)"
    proc = subprocess.run(
        SUBIR_VENTAS,
        shell=True,
        capture_output=True,
        text=True,
        timeout=3600,
        cwd=SUBIR_VENTAS_CWD,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out[:4000]


def main() -> None:
    if CAJA_ID <= 0:
        print("Configura CAJA_ID (entero > 0) en variables de entorno o en el script.", file=sys.stderr)
        sys.exit(1)

    next_url = f"{BASE_URL}/cashier_sync/{CAJA_ID}/next"
    print(f"[caja-pull] CAJA_ID={CAJA_ID} poll={POLL_SECONDS}s URL={next_url}")

    while True:
        try:
            r = requests.get(next_url, headers=_headers(), timeout=60)
            r.raise_for_status()
            data: dict[str, Any] = r.json()
            cmd = data.get("command")
            if not cmd:
                time.sleep(POLL_SECONDS)
                continue

            command_id = cmd["command_id"]
            action = cmd.get("action") or "sync_sales"
            print(f"[caja-pull] Comando recibido id={command_id} action={action}")

            t0 = time.perf_counter()
            code, log_text = ejecutar_subida_ventas()
            ms = int((time.perf_counter() - t0) * 1000)

            complete_url = f"{BASE_URL}/cashier_sync/{CAJA_ID}/commands/{command_id}/complete"
            body: dict[str, Any] = {
                "status": "completado" if code == 0 else "error",
                "resultado": log_text[:2000] if code == 0 else None,
                "error": None if code == 0 else (log_text[:2000] or f"exit {code}"),
                "duration_ms": ms,
            }
            if code != 0:
                body["error"] = body.get("error") or f"Proceso terminó con código {code}"

            cr = requests.post(complete_url, headers=_headers(), json=body, timeout=120)
            cr.raise_for_status()
            print(f"[caja-pull] Reportado al servidor: {cr.json()}")
        except requests.RequestException as e:
            print(f"[caja-pull] Error red: {e}", file=sys.stderr)
        except Exception as e:
            print(f"[caja-pull] Error: {e}", file=sys.stderr)

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
