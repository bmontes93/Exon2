@echo off
title EXON-FACE :: DETENER TODOS LOS SERVICIOS
color 0C
cls
echo ======================================================================
echo           EXON-FACE -- DETENIENDO TODOS LOS SERVICIOS
echo ======================================================================
echo.

echo [*] Cerrando Backend en puerto 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [*] Cerrando Frontend en puerto 3000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo [OK] Todos los servicios han sido cerrados y la memoria fue liberada.
echo.
timeout /t 3
