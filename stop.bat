@echo off
setlocal EnableExtensions
title inspection_system Stop
color 0E

cd /d "%~dp0" || (
    echo ERROR: Could not switch to the project directory.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Stopping inspection_system
echo ============================================================
echo.

where docker >nul 2>nul
if errorlevel 1 (
    echo ERROR: Docker was not found.
    pause
    exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
    echo ERROR: Docker Desktop is not running.
    pause
    exit /b 1
)

echo [1/1] Stopping containers...
docker compose down
if errorlevel 1 (
    echo ERROR: Docker Compose could not stop the services.
    pause
    exit /b 1
)

echo.
echo SUCCESS: System stopped.
echo.
pause
exit /b 0
