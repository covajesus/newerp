import sys
import requests
import json
import time

# Esperar que el servidor esté listo
time.sleep(1)

def test_kardex_endpoint():
    print("🧪 Probando endpoint /kardex_values/ con diferentes payloads")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000"
    
    # Test 1: JSON vacío
    print("\n🔍 Test 1: JSON vacío {}")
    try:
        response = requests.post(f"{base_url}/kardex_values/", 
                               json={}, 
                               timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    
    # Test 2: Solo page
    print("\n🔍 Test 2: Solo page")
    try:
        response = requests.post(f"{base_url}/kardex_values/", 
                               json={"page": 1}, 
                               timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    
    # Test 3: Todos los campos
    print("\n🔍 Test 3: Todos los campos")
    try:
        payload = {
            "page": 1,
            "code": None,
            "product_id": None,
            "branch_office_id": 1,
            "items_per_page": 10
        }
        response = requests.post(f"{base_url}/kardex_values/", 
                               json=payload, 
                               timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    
    # Test 4: Endpoint de prueba simple
    print("\n🔍 Test 4: Endpoint de prueba simple")
    try:
        response = requests.get(f"{base_url}/test/", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    test_kardex_endpoint()
