import urllib.request
import urllib.parse
import json
import time

# Esperar que el servidor esté listo
time.sleep(1)

def test_endpoint(url, method='GET', data=None):
    try:
        if data:
            data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=data, method=method)
            req.add_header('Content-Type', 'application/json')
        else:
            req = urllib.request.Request(url, method=method)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = response.read().decode('utf-8')
            return {
                'status': response.getcode(),
                'data': json.loads(result)
            }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

print("=== Probando endpoint de test simple ===")
result = test_endpoint('http://127.0.0.1:8000/test/')
print(f"Resultado: {json.dumps(result, indent=2)}")

print("\n=== Probando endpoint kardex con datos mínimos ===")
result = test_endpoint('http://127.0.0.1:8000/kardex_values/', 'POST', {'page': 1})
print(f"Resultado: {json.dumps(result, indent=2)}")

print("\n=== Probando endpoint kardex vacío ===")
result = test_endpoint('http://127.0.0.1:8000/kardex_values/', 'POST', {})
print(f"Resultado: {json.dumps(result, indent=2)}")

print("\n=== Probando endpoint kardex con todos los parámetros ===")
result = test_endpoint('http://127.0.0.1:8000/kardex_values/', 'POST', {
    'page': 1,
    'code': None,
    'product_id': None,
    'branch_office_id': 1,
    'items_per_page': 10
})
print(f"Resultado: {json.dumps(result, indent=2)}")
