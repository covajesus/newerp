import requests
import json

# Test del endpoint kardex
url = "http://127.0.0.1:8000/kardex_values/"

# Test 1: Solo con page
data1 = {"page": 1}
print("Test 1 - Solo page:")
print(f"Request: {json.dumps(data1)}")
try:
    response = requests.post(url, json=data1)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*50 + "\n")

# Test 2: Con todos los parámetros opcionales nulos
data2 = {
    "page": 1,
    "code": None,
    "product_id": None,
    "branch_office_id": 1,
    "items_per_page": 10
}
print("Test 2 - Con parámetros nulos:")
print(f"Request: {json.dumps(data2)}")
try:
    response = requests.post(url, json=data2)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*50 + "\n")

# Test 3: Vacío (sin parámetros opcionales)
data3 = {}
print("Test 3 - JSON vacío:")
print(f"Request: {json.dumps(data3)}")
try:
    response = requests.post(url, json=data3)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
