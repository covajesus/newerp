"""
Test directo a API Gateway (sin base de datos)
"""
import requests
import json
from datetime import datetime

print("=" * 80)
print("TEST DIRECTO A API GATEWAY - EMISIÓN BTE")
print("=" * 80)

# Payload de prueba
payload = {
    "auth": {
        "pass": {
            "clave": "",  # Contraseña del SII (dejar vacío si usas certificado)
            "rut": "76063822-9"  # Tu RUT
        }
    },
    "boleta": {
        "Detalle": [
            {
                "MontoItem": 50000,
                "NmbItem": "HONORARIO PROFESIONAL"
            }
        ],
        "Encabezado": {
            "Emisor": {
                "RUTEmisor": "76063822-9"
            },
            "IdDoc": {
                "FchEmis": datetime.now().strftime("%Y-%m-%d")
            },
            "Receptor": {
                "CmnaRecep": "Santiago",
                "DirRecep": "Av. Test 123",
                "RUTRecep": "12345678-9",
                "RznSocRecep": "Juan Perez"
            }
        }
    }
}

print("\nPayload:")
print(json.dumps(payload, indent=2, ensure_ascii=False))

try:
    print("\n1. Enviando request a API Gateway...")
    api_url = "https://www.apigateway.cl/api/v1/sii/bte/emitidas/emitir"
    
    response = requests.post(
        api_url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    print(f"\n2. Status Code: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
    
    print("\n3. Respuesta:")
    try:
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except:
        print(response.text)
    
    if response.status_code == 200 or response.status_code == 201:
        print("\n✓ BOLETA EMITIDA EXITOSAMENTE")
    else:
        print("\n⚠ Error en la emisión")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETADO")
    print("=" * 80)
    
    # Notas importantes
    print("\n📝 NOTAS:")
    print("- Si el error es de autenticación, verifica RUT y contraseña")
    print("- API Gateway requiere cuenta y posiblemente API key")
    print("- Revisa la documentación en: https://www.apigateway.cl/")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    print("\nTraceback:")
    print(traceback.format_exc())
