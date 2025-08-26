import codecs

# Leer el archivo original
with codecs.open(r'app\backend\classes\accountability_class.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Definir reemplazos
replacements = {
    'dÃ­a': 'día',
    'aÃ±o': 'año', 
    'perÃ­odo': 'período',
    'especÃ­fico': 'específico',
    'dÃ©bito': 'débito',
    'informaciÃ³n': 'información',
    'eliminaciÃ³n': 'eliminación',
    'vÃ¡lida': 'válida',
    'vÃ¡lido': 'válido',
    'ParÃ¡metros': 'Parámetros',
    'â ï¸': '⚠️',
    '€': '🤖',
    'âš ': '⚠️ ',
    'âŒ': '❌',
    "—'ï¸": '⚠️',
    'PerÃ­odo': 'Período',
    'fallÃ³': 'falló',
    'MÃ©todo': 'Método',
    'quÃ©': 'qué',
    'despuÃ©s': 'después',
    'AÃºn': 'Aún',
    'tÃ©rminos': 'términos',
    'tÃ©rmino': 'término',
    'EliminaciÃ³n': 'Eliminación',
    '"…': '🔍',
    'Œ': '🔧',
    '¸': '⚠️',
    '""': '🔄',
    '"‹': '📝',
    '§¹': '✅',
    '§ª': '🧪'
}

# Aplicar reemplazos
for old, new in replacements.items():
    content = content.replace(old, new)

# Escribir el archivo corregido
with codecs.open(r'app\backend\classes\accountability_class.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Correcciones aplicadas con éxito')
