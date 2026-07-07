@echo off
setlocal EnableExtensions
title inspection_system Start
color 0A

cd /d "%~dp0" || (
    echo ERROR: Could not switch to the project directory.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Starting inspection_system
echo ============================================================
echo.

where docker >nul 2>nul
if errorlevel 1 (
    echo ERROR: Docker was not found. Install Docker Desktop first.
    pause
    exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
    echo ERROR: Docker Desktop is not running.
    pause
    exit /b 1
)

if not exist ".env" (
    echo ERROR: .env was not found. Run setup.bat first.
    pause
    exit /b 1
)

echo [1/2] Starting containers...
docker compose up -d
if errorlevel 1 (
    echo ERROR: Docker Compose could not start the services.
    pause
    exit /b 1
)

echo.
echo [2/2] Service status:
docker compose ps
echo.
echo SUCCESS: System should be available at http://localhost:8000
set "LAN_IP="
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /R /C:"IPv4 Address"') do if not defined LAN_IP for /f "tokens=* delims= " %%B in ("%%A") do set "LAN_IP=%%B"
if defined LAN_IP echo LAN URL: http://%LAN_IP%:8000
echo.
pause
exit /b 0
