@echo off
REM Wrapper para Windows Task Scheduler (tarea MamayaAlertasLicencias, diaria 12:00).
REM Envia alertas de vencimiento de licencias a los usuarios suscritos.
cd /d "C:\Users\Ariany\Documents\Ariany\proyecto mamaya licencias"
"C:\Users\Ariany\Documents\Ariany\proyecto mamaya licencias\venv\Scripts\python.exe" manage.py enviar_alertas
