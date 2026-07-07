@echo off
setlocal EnableExtensions EnableDelayedExpansion
title inspection_system Windows Setup
color 0A

set "APP_URL=http://localhost:8000"
set "HEALTH_URL=http://localhost:8000/healthz/"

echo.
echo ============================================================
echo  inspection_system - Windows One-Click Installer
echo ============================================================
echo.

cd /d "%~dp0" || (
    echo ERROR: Could not switch to the project directory.
    pause
    exit /b 1
)

echo [1/7] Checking Docker...
where docker >nul 2>nul
if errorlevel 1 (
    echo ERROR: Docker was not found.
    echo Install Docker Desktop, start it, then run setup.bat again.
    pause
    exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
    echo ERROR: Docker Desktop is installed but not running.
    echo Start Docker Desktop and wait until it says Docker is running.
    pause
    exit /b 1
)

docker compose version >nul 2>nul
if errorlevel 1 (
    echo ERROR: docker compose is not available.
    echo Update Docker Desktop to a version that includes Docker Compose v2.
    pause
    exit /b 1
)

echo OK: Docker and Docker Compose are ready.
echo.

echo [2/7] Creating environment file...
if not exist ".env.example" (
    echo ERROR: .env.example was not found in this folder.
    pause
    exit /b 1
)

if not exist ".env" (
    copy ".env.example" ".env" >nul
    if errorlevel 1 (
        echo ERROR: Could not create .env from .env.example.
        pause
        exit /b 1
    )
    echo OK: Created .env from .env.example.
) else (
    echo OK: Existing .env found. Missing or placeholder secrets will be updated.
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $path='.env'; $text=Get-Content -Raw -LiteralPath $path; function New-Secret([int]$bytes) { $buffer=New-Object byte[] $bytes; $rng=[System.Security.Cryptography.RandomNumberGenerator]::Create(); try { $rng.GetBytes($buffer) } finally { $rng.Dispose() }; [Convert]::ToBase64String($buffer).TrimEnd('=').Replace('+','-').Replace('/','_') }; function Set-EnvValue([string]$name,[string]$value) { $script:text = [regex]::Replace($script:text, '(?m)^' + [regex]::Escape($name) + '=.*$', $name + '=' + $value); if ($script:text -notmatch ('(?m)^' + [regex]::Escape($name) + '=')) { $script:text = $script:text.TrimEnd() + [Environment]::NewLine + $name + '=' + $value + [Environment]::NewLine } }; function Get-EnvValue([string]$name) { $m=[regex]::Match($script:text, '(?m)^' + [regex]::Escape($name) + '=(.*)$'); if ($m.Success) { return $m.Groups[1].Value.Trim() }; return '' }; $secret=Get-EnvValue 'DJANGO_SECRET_KEY'; if ([string]::IsNullOrWhiteSpace($secret) -or $secret -eq 'CHANGE_ME') { Set-EnvValue 'DJANGO_SECRET_KEY' (New-Secret 48) }; $password=Get-EnvValue 'DB_PASSWORD'; if ([string]::IsNullOrWhiteSpace($password) -or $password -eq 'CHANGE_ME') { Set-EnvValue 'DB_PASSWORD' (New-Secret 32) }; if ([string]::IsNullOrWhiteSpace((Get-EnvValue 'DB_NAME'))) { Set-EnvValue 'DB_NAME' 'inspection_system' }; if ([string]::IsNullOrWhiteSpace((Get-EnvValue 'DB_USER'))) { Set-EnvValue 'DB_USER' 'inspection_user' }; if ([string]::IsNullOrWhiteSpace((Get-EnvValue 'DB_HOST'))) { Set-EnvValue 'DB_HOST' 'db' }; if ([string]::IsNullOrWhiteSpace((Get-EnvValue 'DB_PORT'))) { Set-EnvValue 'DB_PORT' '5432' }; Set-Content -LiteralPath $path -Value $text -Encoding ASCII"
if errorlevel 1 (
    echo ERROR: Could not update .env with generated secrets.
    pause
    exit /b 1
)
echo OK: Environment is ready.
echo.

echo [3/7] Checking port 8000...
netstat -ano -p tcp | findstr /R /C:":8000 .*LISTENING" >nul 2>nul
if not errorlevel 1 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -UseBasicParsing -Uri '%HEALTH_URL%' -TimeoutSec 5 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>nul
    if errorlevel 1 (
        echo ERROR: Port 8000 is already in use by another program.
        echo Close the program using port 8000, then run setup.bat again.
        pause
        exit /b 1
    ) else (
        echo OK: Port 8000 is already serving this application's health endpoint.
    )
) else (
    echo OK: Port 8000 is available.
)
echo.

echo [4/7] Building containers...
docker compose build
if errorlevel 1 (
    echo ERROR: Docker build failed.
    pause
    exit /b 1
)
echo.

echo [5/7] Starting containers...
docker compose up -d
if errorlevel 1 (
    echo ERROR: Docker Compose could not start the services.
    echo Run docker compose logs for details after fixing the problem.
    pause
    exit /b 1
)
echo.

echo [6/7] Preparing Django database and static files...
docker compose exec -T web python manage.py migrate
if errorlevel 1 (
    echo ERROR: Django migrations failed.
    pause
    exit /b 1
)

docker compose exec -T web python manage.py collectstatic --noinput
if errorlevel 1 (
    echo ERROR: Django collectstatic failed.
    pause
    exit /b 1
)
echo.

echo [7/7] Verifying system health...
set "HEALTH_OK=0"
for /L %%I in (1,1,30) do (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -UseBasicParsing -Uri '%HEALTH_URL%' -TimeoutSec 5 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>nul
    if not errorlevel 1 (
        set "HEALTH_OK=1"
        goto health_done
    )
    echo Waiting for web service... %%I/30
    timeout /t 2 /nobreak >nul
)

:health_done
if not "%HEALTH_OK%"=="1" (
    echo ERROR: The application did not pass the health check at %HEALTH_URL%.
    echo Showing current container status:
    docker compose ps
    pause
    exit /b 1
)

echo OK: Health check passed.
echo.
echo Opening browser...
start "" "%APP_URL%"
echo.
echo SUCCESS: System is running at %APP_URL%
set "LAN_IP="
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /R /C:"IPv4 Address"') do if not defined LAN_IP for /f "tokens=* delims= " %%B in ("%%A") do set "LAN_IP=%%B"
if defined LAN_IP echo LAN URL: http://%LAN_IP%:8000
echo.
pause
exit /b 0
