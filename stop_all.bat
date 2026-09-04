@echo off
title EXON-FACE :: DETENER TODOS LOS PROCESOS
color 0C
echo ======================================================================
echo           EXON-FACE -- DETENIENDO TODOS LOS SERVICIOS
echo ======================================================================
echo.

echo [*] Buscando y cerrando procesos en puerto 8000 (Backend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo    -> Cerrando PID %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo [*] Buscando y cerrando procesos en puerto 3000 (Frontend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    echo    -> Cerrando PID %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo [OK] Todos los servicios han sido cerrados limpiamente. Memoria liberada.
echo.
timeout /t 3
