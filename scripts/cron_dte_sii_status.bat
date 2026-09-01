@echo off
REM Cron IntraJIS: sincroniza estados SII de DTE emitidos (cada 20 min vía Task Scheduler)
cd /d "%~dp0\.."
python "%~dp0cron_dte_sii_status.py" >> "%~dp0..\logs\cron_dte_sii_status.log" 2>&1
