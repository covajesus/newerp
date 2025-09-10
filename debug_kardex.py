import json
import subprocess
import time

# Esperar un momento para que el servidor esté listo
time.sleep(2)

# Probar con curl directamente
curl_command = [
    'curl', 
    '-X', 'POST',
    'http://127.0.0.1:8000/kardex_values/',
    '-H', 'Content-Type: application/json',
    '-d', '{"page": 1}'
]

try:
    result = subprocess.run(curl_command, capture_output=True, text=True, timeout=10)
    print("Status Code:", result.returncode)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
except subprocess.TimeoutExpired:
    print("Request timed out")
except Exception as e:
    print(f"Error running curl: {e}")

print("\n" + "="*50 + "\n")

# Probar el endpoint de test simple
curl_test_command = [
    'curl', 
    '-X', 'GET',
    'http://127.0.0.1:8000/test/'
]

try:
    result = subprocess.run(curl_test_command, capture_output=True, text=True, timeout=10)
    print("Test Endpoint Status Code:", result.returncode)
    print("Test Endpoint STDOUT:", result.stdout)
    print("Test Endpoint STDERR:", result.stderr)
except subprocess.TimeoutExpired:
    print("Test request timed out")
except Exception as e:
    print(f"Error running test curl: {e}")
