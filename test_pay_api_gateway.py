"""
Test del endpoint /honoraries/pay con API Gateway
"""
import requests
import json

print("=" * 80)
print("TEST DE EMISIÓN DE BOLETA - API GATEWAY")
print("=" * 80)

# URL del backend local
base_url = "http://127.0.0.1:8000"

# Datos de prueba - ajusta el ID según un honorario real en tu BD
test_payload = {
    "id": 1,  # Cambia esto por un ID real de honorary
    "period": "2025-11",
    "expense_type_id": 1  # Cambia esto por un expense_type_id real
}

print("\nPayload de prueba:")
print(json.dumps(test_payload, indent=2))

try:
    print("\n1. Enviando request a /honoraries/pay...")
    response = requests.post(
        f"{base_url}/honoraries/pay",
        json=test_payload,
        timeout=30
    )
    
    print(f"\n2. Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n3. Respuesta:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get("success"):
            print("\n✓ BOLETA EMITIDA EXITOSAMENTE")
        else:
            print("\n⚠ Error en la emisión")
            print(f"Error: {result.get('error')}")
    else:
        print(f"\n❌ Error HTTP: {response.status_code}")
        print(f"Respuesta: {response.text}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETADO")
    print("=" * 80)
    
except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: No se pudo conectar al servidor")
    print("Asegúrate de que el backend esté corriendo en http://127.0.0.1:8000")
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    print("\nTraceback:")
    print(traceback.format_exc())
