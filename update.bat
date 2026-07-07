@echo off
setlocal EnableExtensions
title inspection_system Update
color 0B

cd /d "%~dp0" || (
    echo ERROR: Could not switch to the project directory.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Updating inspection_system
echo ============================================================
echo.

where git >nul 2>nul
if errorlevel 1 (
    echo ERROR: Git was not found. Install Git for Windows first.
    pause
    exit /b 1
)

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

echo [1/4] Pulling latest code...
git pull
if errorlevel 1 (
    echo ERROR: git pull failed. Resolve the Git issue, then run update.bat again.
    pause
    exit /b 1
)

echo.
echo [2/4] Rebuilding containers without cache...
docker compose build --no-cache
if errorlevel 1 (
    echo ERROR: Docker rebuild failed.
    pause
    exit /b 1
)

echo.
echo [3/4] Starting updated containers...
docker compose up -d
if errorlevel 1 (
    echo ERROR: Docker Compose could not start the updated services.
    pause
    exit /b 1
)

echo.
echo [4/4] Service status:
docker compose ps
echo.
echo SUCCESS: System updated and running at http://localhost:8000
set "LAN_IP="
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /R /C:"IPv4 Address"') do if not defined LAN_IP for /f "tokens=* delims= " %%B in ("%%A") do set "LAN_IP=%%B"
if defined LAN_IP echo LAN URL: http://%LAN_IP%:8000
echo.
pause
exit /b 0
