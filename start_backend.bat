@echo off
title EXON-FACE :: BACKEND SERVER (FastAPI)
color 0A
echo ======================================================================
echo           EXON-FACE -- INICIANDO MOTOR BACKEND DE IA
echo ======================================================================
echo.

:: Liberar puerto 8000 si hubiera algun proceso zombie
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo [*] Liberando puerto 8000 (PID %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

cd /d "d:\EXON2\backend"
echo [*] Directorio de Trabajo: %CD%
echo [*] Directorio de Modelos: D:\EXON2\models
echo [*] Endpoint API         : http://127.0.0.1:8000
echo [*] Documentacion Swagger: http://127.0.0.1:8000/docs
echo.
echo ======================================================================
echo           PRESIONA CTRL+C EN ESTA VENTANA PARA DETENER
echo ======================================================================
echo.

.venv_cuda\Scripts\python.exe -m uvicorn src.interfaces.api.app:create_app --factory --host 127.0.0.1 --port 8000
pause
