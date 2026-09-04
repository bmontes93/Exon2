@echo off
title EXON-FACE :: LANZADOR MAESTRO
color 0E
echo ======================================================================
echo           EXON-FACE -- INICIANDO PLATAFORMA COMPLETA
echo ======================================================================
echo.

:: 1. Limpieza de puertos previos
echo [*] Verificando y liberando puertos previos...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: 2. Iniciar Backend FastAPI en ventana independiente
echo [*] Levantando Backend (FastAPI :8000)...
start "EXON-FACE BACKEND (:8000)" cmd /k "cd /d d:\EXON2\backend && python -m uvicorn src.interfaces.api.app:create_app --factory --host 127.0.0.1 --port 8000"

:: 3. Esperar 3 segundos para inicialización de API
timeout /t 3 /nobreak >nul

:: 4. Iniciar Frontend Next.js en ventana independiente
echo [*] Levantando Frontend (Next.js :3000)...
start "EXON-FACE FRONTEND (:3000)" cmd /k "cd /d d:\EXON2\frontend && npm run dev"

:: 5. Esperar y abrir navegador
timeout /t 4 /nobreak >nul
echo [*] Abriendo navegador en http://localhost:3000/studio ...
start http://localhost:3000/studio

echo.
echo ======================================================================
echo  [OK] Plataforma iniciada con exito en ventanas independientes.
echo  - Puedes minimizar las ventanas de consola.
echo  - Para detener todo de golpe, ejecuta stop_all.bat
echo ======================================================================
echo.
timeout /t 5
