# Instrucciones para Soporte API Gateway - Error BTE

**Fecha:** 12 de noviembre de 2025  
**Problema:** Error 409 - Timeout al emitir Boletas de Honorarios Electrónicas (BTE)  
**Soporte:** Derafu Helpdesk Support

---

## Información Solicitada

El equipo de soporte de API Gateway solicita los siguientes datos para investigar el problema:

### 1. Request enviada a la API (Cuerpo completo)

**URL usada:**
```
POST https://legacy.apigateway.cl/api/v1/sii/bte/emitidas/emitir
```

**Headers:**
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer {APIGATEWAY_TOKEN}"
}
```

**Body (Payload):**
```json
{
  "auth": {
    "pass": {
      "clave": "JYM1",
      "rut": "76063822-9"
    }
  },
  "boleta": {
    "Detalle": [
      {
        "MontoItem": 584795,
        "NmbItem": "HONORARIO"
      }
    ],
    "Encabezado": {
      "Emisor": {
        "RUTEmisor": "76063822-9"
      },
      "IdDoc": {
        "FchEmis": "2025-11-12"
      },
      "Receptor": {
        "CmnaRecep": "SANTIAGO",
        "DirRecep": "CALLE EJEMPLO 123",
        "RUTRecep": "12345678-9",
        "RznSocRecep": "JUAN PEREZ GONZALEZ"
      }
    }
  }
}
```

### 2. Response exacto de la API

**Status Code:** `409 Conflict`

**Response Body:**
```json
{
  "message": "cURL error 28: Connection timed out after 20001 milliseconds (see https://curl.haxx.se/libcurl/c/libcurl-errors.html) for https://api.sii.cl/bte/emision"
}
```

### 3. Contexto Adicional

- **Frecuencia del error:** Intermitente, no ocurre en todos los intentos
- **Timeout configurado en cliente:** 90 segundos
- **Reintentos implementados:** 3 intentos con delays de 5, 10, 15 segundos
- **Proxy configurado:** Pendiente de configuración
- **Horario de mayor incidencia:** No determinado aún

---

## Notas del SII

Según el soporte, **el SII está presentando intermitencias en la emisión de BTE**. Esto puede estar relacionado con:

1. Alta demanda en los servicios del SII
2. Timeouts en la infraestructura del SII (>20 segundos)
3. Restricciones de IP o rate limiting

---

## Acciones Tomadas

1. ✅ Aumentado timeout de cliente de 30s a 90s
2. ✅ Implementado sistema de reintentos (3 intentos)
3. ✅ Preparada configuración de proxy HTTP
4. ⏳ Pendiente: Desplegar proxy Squid en servidor dedicado
5. ⏳ Pendiente: Configurar proxy en plataforma API Gateway

---

## Próximos Pasos

1. **Recopilar logs detallados** con timestamp exacto de cada intento fallido
2. **Configurar proxy** siguiendo `PROXY_SETUP.md`
3. **Enviar información al soporte** cuando ocurra el próximo error
4. **Monitorear header** `X-Stats-HttpClientProxy` en las respuestas (1=proxy usado, 0=no usado)

---

## Script para Capturar Información

Para facilitar la recopilación de datos, puedes usar el siguiente script:

```python
# test_honorary_detailed_logging.py
import requests
import json
from datetime import datetime

# Ejecutar prueba con logging detallado
api_url = "https://legacy.apigateway.cl/api/v1/sii/bte/emitidas/emitir"
token = "TU_TOKEN_AQUI"

payload = {
    # ... tu payload completo
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

print(f"{'='*80}")
print(f"TIMESTAMP: {datetime.now().isoformat()}")
print(f"{'='*80}")
print(f"\nREQUEST URL:\n{api_url}")
print(f"\nREQUEST HEADERS:\n{json.dumps(headers, indent=2)}")
print(f"\nREQUEST BODY:\n{json.dumps(payload, indent=2)}")

try:
    response = requests.post(api_url, json=payload, headers=headers, timeout=90)
    
    print(f"\n{'='*80}")
    print(f"RESPONSE STATUS: {response.status_code}")
    print(f"{'='*80}")
    print(f"\nRESPONSE HEADERS:\n{dict(response.headers)}")
    print(f"\nRESPONSE BODY:\n{response.text}")
    
except Exception as e:
    print(f"\n{'='*80}")
    print(f"EXCEPTION: {type(e).__name__}")
    print(f"{'='*80}")
    print(f"\nERROR: {str(e)}")
```

---

## Contacto Soporte

**Correo:** [Dirección del soporte de API Gateway]  
**Asunto:** Error 409 - Timeout en emisión de BTE  
**Prioridad:** Alta (servicio intermitente)

---

## Referencias

- Documentación: `PROXY_SETUP.md`
- Cambios realizados: `CAMBIOS_PROXY.md`
- Script de prueba: `test_honorary_send.py`
- Código fuente: `app/backend/classes/honorary_class.py` (método `send()`)
