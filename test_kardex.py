import urllib.request
import json
import time

# Esperar que el servidor esté listo
time.sleep(2)

print("🧪 Probando endpoint /kardex_values/ corregido")
print("=" * 60)

# Test con JSON vacío
try:
    data = json.dumps({}).encode('utf-8')
    req = urllib.request.Request(
        'http://127.0.0.1:8000/kardex_values/', 
        data=data, 
        method='POST'
    )
    req.add_header('Content-Type', 'application/json')
    
    with urllib.request.urlopen(req, timeout=10) as response:
        result = response.read().decode('utf-8')
        parsed_result = json.loads(result)
        
        print(f"✅ Status Code: {response.getcode()}")
        print(f"📊 Response:")
        print(json.dumps(parsed_result, indent=2, ensure_ascii=False))
        
        # Verificar si hay datos
        if 'message' in parsed_result and 'data' in parsed_result['message']:
            data_list = parsed_result['message']['data']
            print(f"\n📈 Resumen:")
            print(f"   - Total items: {parsed_result['message'].get('total_items', 0)}")
            print(f"   - Items en esta página: {len(data_list)}")
            if data_list:
                print(f"   - Primer producto: {data_list[0].get('name', 'N/A')}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)

# Test del endpoint de verificación de base de datos
print("\n🔍 Probando endpoint de verificación de BD")
try:
    req = urllib.request.Request('http://127.0.0.1:8000/test/database-check')
    
    with urllib.request.urlopen(req, timeout=10) as response:
        result = response.read().decode('utf-8')
        parsed_result = json.loads(result)
        
        print(f"✅ Status Code: {response.getcode()}")
        print(f"📊 Database Check:")
        print(json.dumps(parsed_result, indent=2, ensure_ascii=False))
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n✨ Prueba completada")
