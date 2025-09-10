import urllib.request
import json
import time

time.sleep(1)

def test_endpoint(url, method='GET', data=None):
    try:
        if data:
            data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=data, method=method)
            req.add_header('Content-Type', 'application/json')
        else:
            req = urllib.request.Request(url, method=method)
        
        with urllib.request.urlopen(req, timeout=5) as response:
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

print("=== Probando servidor simple ===")
result = test_endpoint('http://127.0.0.1:8001/')
print(f"GET /: {json.dumps(result, indent=2)}")

result = test_endpoint('http://127.0.0.1:8001/test-kardex', 'POST', {})
print(f"POST /test-kardex: {json.dumps(result, indent=2)}")
