@echo off
REM Coloca este archivo en C:\boleta junto con caja_pull_sync_agent.py y tu script de subida (sql.py en la misma carpeta).
REM Edita CAJA_ID y el nombre del .py de envío si no es enviar_recaudacion.py

cd /d C:\boleta

set CAJA_ID=0
REM Cambia 0 por el ID numérico de esta caja en el ERP
set CAJA_SYNC_API_BASE=https://intrajisbackend.com/api
set CAJA_SUBIR_VENTAS_CWD=C:\boleta
set CAJA_SUBIR_VENTAS_CMD=python C:\boleta\enviar_recaudacion.py
REM Si tu archivo tiene otro nombre, cámbialo arriba (ej. subir_ventas.py)

REM Opcional: mismo token que CASHIER_SYNC_API_TOKEN en el servidor (.env). Si no usas token, deja la línea comentada.
REM set CAJA_SYNC_API_TOKEN=

set CAJA_SYNC_POLL_SECONDS=10

python C:\boleta\caja_pull_sync_agent.py
pause
