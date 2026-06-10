import json
import requests

swagger = requests.get("https://api.simplefactura.cl/swagger/v1/swagger.json", timeout=30).json()
path = swagger["paths"].get("/invoiceV2/{sucursal}", {})
print(json.dumps(path, indent=2)[:4000])
