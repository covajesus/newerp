import re

# Leer el archivo
with open(r'app\backend\classes\accountability_class.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Definir los reemplazos necesarios para las líneas 985-1060 (primer bucle assets que usa asiento incorrectamente)
replacements_first_section = [
    ('delete_url = f"https://libredte.cl/api/lce/lce_asientos/eliminar/{year}/{codigo_asiento}/76063822"', 
     'delete_url = f"https://libredte.cl/api/lce/lce_asientos/eliminar/{year}/{codigo_asset}/76063822"'),
    ('delete_url_alt = f"https://libredte.cl/api/lce/lce_asientos/eliminar/2025/{codigo_asiento}/76063822"',
     'delete_url_alt = f"https://libredte.cl/api/lce/lce_asientos/eliminar/2025/{codigo_asset}/76063822"'),
    ('"codigo": codigo_asiento,',
     '"codigo": codigo_asset,'),
    ('print(f"✅ Eliminado asiento de ingresos: {codigo_asiento}")',
     'print(f"🔍 Eliminado asset de ingresos: {codigo_asset}")'),
    ('print(f"❌ No se pudo eliminar asiento: {codigo_asiento} - Status: {delete_response.status_code}")',
     'print(f"❌ No se pudo eliminar asset: {codigo_asset} - Status: {delete_response.status_code}")'),
    ('                                "asiento": asiento',
     '                                "asset": asset'),
    ('                        print(f"⏭️ Asiento no cumple criterios para eliminación")',
     '                        print(f"⏭️ Asset no cumple criterios para eliminación"'),
    ('                    print(f"⚠️ Asiento no tiene estructura válida: {asiento}")',
     '                    print(f"⚠️ Asset no tiene estructura válida: {asset}')
]

# Solo reemplazar las primeras instancias (en el primer bucle)
for old, new in replacements_first_section:
    # Reemplazar solo la primera ocurrencia
    content = content.replace(old, new, 1)

# Para otros reemplazos específicos en contexto, necesitamos también corregir las referencias a asiento_id
content = content.replace('asiento_id = asiento[\'id\']  # \'2025-28435\'', 'asset_id = asset[\'id\']  # \'2025-28435\'', 1)
content = content.replace('delete_url_id = f"https://libredte.cl/api/lce/lce_asientos/eliminar/{asiento_id}/76063822"', 'delete_url_id = f"https://libredte.cl/api/lce/lce_asientos/eliminar/{asset_id}/76063822"', 1)

# Guardar el archivo
with open(r'app\backend\classes\accountability_class.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Correcciones aplicadas en el primer bucle de assets")
