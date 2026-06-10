"""Compare biller script vs newerp v2 emit against SimpleFactura invoiceV2."""
import json
import time
from datetime import datetime, timedelta

import requests

TIMEOUT = 25
URL = "https://api.simplefactura.cl/invoiceV2/Casa_Matriz"
BASIC_AUTH = "Basic cm9kcmlnb2NhYmV6YXNAamlzcGFya2luZy5jb206Um9ybzIwMjQu"

today = datetime.now().date()
added_date_str = today.strftime("%Y-%m-%d")
due_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")
total = 1190
subtotal = round(total / 1.19)
tax = total - subtotal
test_folio = 999999998  # test folio — do not use in prod billing loop

# --- Exact biller payload ---
biller_payload = {
    "Documento": {
        "Encabezado": {
            "IdDoc": {
                "TipoDTE": 39,
                "FchEmis": added_date_str,
                "FchVenc": due_date,
                "Folio": test_folio,
                "IndServicio": 3,
                "IndMntNeto": 2,
            },
            "Emisor": {
                "RUTEmisor": "76063822-6",
                "RznSocEmisor": "Jisparking SpA",
                "GiroEmisor": "ESTACIONAMIENTO DE VEHÍCULOS Y PARQUÍMETROS, VENTA DE PRODUCTOS  FARMACEUTICOS",
                "DirOrigen": "Matucana 40",
                "CmnaOrigen": "Santiago",
            },
            "Receptor": {
                "RUTRecep": "66666666-6",
                "RznSocRecep": "Cliente en Sucursal",
            },
            "Totales": {
                "MntNeto": subtotal,
                "IVA": tax,
                "MntTotal": total,
            },
        },
        "Detalle": [
            {
                "NroLinDet": "1",
                "NmbItem": "Estacionamiento TEST - PRUEBA",
                "QtyItem": "1",
                "UnmdItem": "un",
                "PrcItem": subtotal,
                "MontoItem": subtotal,
            }
        ],
    }
}

biller_headers = {
    "Authorization": BASIC_AUTH,
    "Content-Type": "application/json",
}

# --- newerp v2 payload (abonado, sin Folio, receptor real) ---
newerp_document = {
    "Encabezado": {
        "IdDoc": {
            "TipoDTE": 39,
            "FchEmis": added_date_str,
            "FchVenc": due_date,
            "IndServicio": 3,
            "IndMntNeto": 2,
        },
        "Emisor": {
            "RUTEmisor": "76063822-6",
            "RznSocEmisor": "Jisparking SpA",
            "GiroEmisor": "ESTACIONAMIENTO DE VEHÍCULOS Y PARQUÍMETROS, VENTA DE PRODUCTOS  FARMACEUTICOS",
            "DirOrigen": "Matucana 40",
            "CmnaOrigen": "Santiago",
        },
        "Receptor": {
            "RUTRecep": "10033721-5",
            "RznSocRecep": "Cliente Prueba",
        },
        "Totales": {
            "MntNeto": subtotal,
            "IVA": tax,
            "MntTotal": total,
        },
    },
    "Detalle": [
        {
            "NroLinDet": "1",
            "NmbItem": " Prestación de estacionamientos. Fecha:" + datetime.now().strftime("%d-%m-%Y"),
            "QtyItem": "1",
            "UnmdItem": "un",
            "PrcItem": subtotal,
            "MontoItem": subtotal,
        }
    ],
}
newerp_payload = {"Documento": newerp_document}


def get_bearer_token():
    r = requests.post(
        "https://api.simplefactura.cl/token",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"email": "jesuscova@jisparking.com", "password": "Jgames88!"}),
        timeout=TIMEOUT,
    )
    print(f"TOKEN endpoint: HTTP {r.status_code} in {r.elapsed.total_seconds():.2f}s")
    if r.status_code != 200:
        print(r.text[:300])
        return None
    return r.json().get("accessToken")


def run_test(label, headers, payload, use_data_param=True):
    print(f"\n=== {label} ===")
    t0 = time.time()
    try:
        if use_data_param:
            response = requests.post(
                URL,
                data=json.dumps(payload),
                headers=headers,
                timeout=TIMEOUT,
            )
        else:
            response = requests.post(
                URL,
                json=payload,
                headers=headers,
                timeout=TIMEOUT,
            )
        elapsed = time.time() - t0
        print(f"HTTP {response.status_code} in {elapsed:.2f}s")
        text = (response.text or "").strip()
        print(f"Body: {text[:600] if text else '(empty)'}")
        if text:
            try:
                data = response.json()
                print(f"status={data.get('status')} message={data.get('message')} errors={data.get('errors')}")
            except ValueError:
                pass
    except requests.Timeout:
        elapsed = time.time() - t0
        print(f"TIMEOUT after {elapsed:.2f}s (limit {TIMEOUT}s)")
    except requests.RequestException as exc:
        elapsed = time.time() - t0
        print(f"ERROR after {elapsed:.2f}s: {exc}")


if __name__ == "__main__":
    print("URL:", URL)
    run_test("BILLER (Basic + data=json.dumps)", biller_headers, biller_payload, use_data_param=True)

    token = get_bearer_token()
    if token:
        bearer_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        run_test("NEWERP (Bearer + data=json.dumps)", bearer_headers, newerp_payload, use_data_param=True)
        run_test("NEWERP (Bearer + json=)", bearer_headers, newerp_payload, use_data_param=False)

    # Biller auth but newerp payload (isolate auth vs payload)
    run_test("HYBRID (Basic auth + newerp payload)", biller_headers, newerp_payload, use_data_param=True)
