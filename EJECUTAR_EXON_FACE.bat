@echo off
title EXON-FACE :: INICIANDO APLICACION (CUDA RTX 3070)
color 0B
cls
echo ======================================================================
echo             EXON-FACE -- SISTEMA DE SINTESIS FACIAL 3D
echo            ACELERACION: NVIDIA GEFORCE RTX 3070 (CUDA 12.1)
echo ======================================================================
echo.
echo [*] 1/3 - Limpiando puertos y procesos anteriores...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [*] 2/3 - Iniciando Motor Backend con PyTorch CUDA 12.1 (:8000)...
start "EXON-FACE BACKEND (CUDA)" cmd /k "cd /d D:\EXON2\backend && .venv_cuda\Scripts\python.exe -m uvicorn src.interfaces.api.app:create_app --factory --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul

echo [*] 3/3 - Iniciando Interfaz Frontend (Next.js :3000)...
start "EXON-FACE FRONTEND" cmd /k "cd /d D:\EXON2\frontend && npm run dev"

echo.
echo [*] Esperando inicializacion de servicios...
timeout /t 4 /nobreak >nul

echo [*] Abriendo EXON-FACE Studio en tu navegador...
start http://localhost:3000/studio

echo.
echo ======================================================================
echo  [OK] EXON-FACE esta corriendo con soporte completo de GPU NVIDIA.
echo.
echo  - Puedes minimizar las ventanas de consola (no las cierres mientras uses la app).
echo  - Para apagar todo cuando termines, usa DETENER_EXON_FACE.bat
echo ======================================================================
echo.
timeout /t 5
