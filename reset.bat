@echo off
setlocal EnableExtensions
title inspection_system Reset
color 0C

cd /d "%~dp0" || (
    echo ERROR: Could not switch to the project directory.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  RESET inspection_system
echo ============================================================
echo.
echo WARNING: This will stop containers and delete Docker volumes.
echo WARNING: The PostgreSQL database data for this project will be removed.
echo WARNING: Docker's build cache and unused resources may also be pruned.
echo.
set /p CONFIRM=Type RESET to continue: 
if not "%CONFIRM%"=="RESET" (
    echo Reset cancelled.
    pause
    exit /b 0
)

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

echo.
echo [1/2] Removing containers and project volumes...
docker compose down -v
if errorlevel 1 (
    echo ERROR: Docker Compose reset failed.
    pause
    exit /b 1
)

echo.
echo [2/2] Pruning unused Docker resources...
docker system prune -f
if errorlevel 1 (
    echo ERROR: Docker system prune failed.
    pause
    exit /b 1
)

echo.
echo SUCCESS: Reset complete. Run setup.bat to reinstall.
echo.
pause
exit /b 0
