# erp_jis_backend_project
Jisparking ERP combina HR, ventas, abonados, recaudaciones y contratos para una gestión eficiente de estacionamientos y activos.

## 🚨 Configuración Importante: Proxy para API Gateway

Si experimentas errores de timeout al emitir boletas de honorarios (Error 409), necesitas configurar un proxy Squid para evitar restricciones del SII.

**📋 Consulta la guía completa:** [PROXY_SETUP.md](./PROXY_SETUP.md)

### Inicio rápido:

```bash
cd proxy-setup
./setup.sh  # Linux/Mac
```

Para más información sobre la configuración del proxy, consulta el directorio `proxy-setup/`.

---
