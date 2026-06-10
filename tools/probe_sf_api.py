import json
import re
import requests

paths = [
    "https://api.simplefactura.cl/swagger/v1/swagger.json",
    "https://api.simplefactura.cl/openapi.json",
]
for path in paths:
    try:
        r = requests.get(path, timeout=10)
        print(path, r.status_code, len(r.text))
        if r.status_code == 200:
            for m in sorted(set(re.findall(r'"(/[^"]*invoice[^"]*)"', r.text, re.I))):
                print(" ", m)
    except Exception as exc:
        print(path, exc)
