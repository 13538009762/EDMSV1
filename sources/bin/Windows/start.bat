@echo off
setlocal EnableDelayedExpansion

:: EDMS Docker Startup Script for Windows
:: This script starts the EDMS containers using files in bin/ directory

set SCRIPT_DIR=%~dp0
set DOCKER_DIR=%SCRIPT_DIR%..\..\docker\
set COMPOSE_FILE=%SCRIPT_DIR%..\docker-compose.yml
set ENV_FILE=%SCRIPT_DIR%..\.env
set DATA_DIR=%SCRIPT_DIR%..\data
set IMAGES_DIR=%SCRIPT_DIR%..\images

echo ============================================
echo    EDMS Docker Startup Script
echo ============================================
echo.

:: Check if Docker is installed
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker is not installed or not in PATH
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

:: Check if Docker is running
docker info >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker daemon is not running
    echo Please start Docker Desktop and try again
    pause
    exit /b 1
)

echo [OK] Docker is running
echo.

:: Check if docker-compose is available
where docker-compose >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set COMPOSE_CMD=docker-compose
) else (
    docker compose version >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set COMPOSE_CMD=docker compose
    ) else (
        echo ERROR: docker-compose is not installed
        pause
        exit /b 1
    )
)

:: Check if .env file exists in bin/ directory
if not exist "%ENV_FILE%" (
    echo ERROR: .env file not found in bin/ directory!
    echo Please run docker/build.bat first to initialize the environment.
    echo.
    echo Expected location: %ENV_FILE%
    pause
    exit /b 1
)

:: Check if data directory exists in bin/ directory
if not exist "%DATA_DIR%" (
    echo ERROR: Data directory not found in bin/ directory!
    echo Please run docker/build.bat first to initialize the environment.
    echo.
    pause
    exit /b 1
)

:: Check if images exist, import if needed
echo Checking Docker images...
docker images --format "{{.Repository}}:{{.Tag}}" | findstr "edms-backend:latest" >nul 2>nul
set BACKEND_EXISTS=%ERRORLEVEL%

docker images --format "{{.Repository}}:{{.Tag}}" | findstr "edms-frontend:latest" >nul 2>nul
set FRONTEND_EXISTS=%ERRORLEVEL%

if %BACKEND_EXISTS% NEQ 0 (
    echo edms-backend image not found, checking for export file...
    if exist "%IMAGES_DIR%\edms-backend.tar" (
        echo Importing edms-backend from %IMAGES_DIR%\edms-backend.tar...
        docker load -i "%IMAGES_DIR%\edms-backend.tar"
        echo [OK] edms-backend imported
    ) else (
        echo ERROR: edms-backend image not found and no export file available
        echo Please run docker/build.bat first to build and export images.
        pause
        exit /b 1
    )
) else (
    echo [OK] edms-backend image exists
)

if %FRONTEND_EXISTS% NEQ 0 (
    echo edms-frontend image not found, checking for export file...
    if exist "%IMAGES_DIR%\edms-frontend.tar" (
        echo Importing edms-frontend from %IMAGES_DIR%\edms-frontend.tar...
        docker load -i "%IMAGES_DIR%\edms-frontend.tar"
        echo [OK] edms-frontend imported
    ) else (
        echo ERROR: edms-frontend image not found and no export file available
        echo Please run docker/build.bat first to build and export images.
        pause
        exit /b 1
    )
) else (
    echo [OK] edms-frontend image exists
)

echo.

:: Check container status
echo Checking container status...
%COMPOSE_CMD% -f "%COMPOSE_FILE%" ps >nul 2>nul
set PS_OUTPUT=
for /f "delims=" %%i in ('%COMPOSE_CMD% -f "%COMPOSE_FILE%" ps 2^>nul') do (
    set "PS_OUTPUT=!PS_OUTPUT! %%i"
)

:: Check if there are any running containers (look for "Up" in output)
echo !PS_OUTPUT! | findstr /C:"Up " >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Services are already running
    echo.
    echo Container status:
    %COMPOSE_CMD% -f "%COMPOSE_FILE%" ps
    echo.
    echo To restart: %COMPOSE_CMD% -f "%COMPOSE_FILE%" restart
    pause
    exit /b 0
) else (
    echo Containers not found. Starting services...
    echo.
    
    :: Start containers (capture output but don't fail on stderr)
    %COMPOSE_CMD% -f "%COMPOSE_FILE%" up -d 2>&1 | findstr /C:"Creating" /C:"Starting" /C:"Started" /C:"Created"
    
    :: Wait for containers to start
    timeout /t 5 /nobreak >nul
    
    :: Verify containers are actually running (use different approach)
    for /f "tokens=*" %%a in ('%COMPOSE_CMD% -f "%COMPOSE_FILE%" ps -q 2^>nul') do (
        set CONTAINER_COUNT=1
    )
    
    if defined CONTAINER_COUNT (
        echo.
        echo [OK] Containers started successfully
    ) else (
        echo.
        echo ERROR: Failed to start containers
        pause
        exit /b 1
    )
)

echo.
echo ============================================
echo    EDMS Deployment Complete!
echo ============================================
echo.
echo Access the application at:
echo   Frontend: http://localhost
echo   Backend API: http://localhost/api
echo.
echo To view logs:
echo   %COMPOSE_CMD% -f "%COMPOSE_FILE%" logs -f
echo.
echo To stop services:
echo   %COMPOSE_CMD% -f "%COMPOSE_FILE%" down
echo.
echo To restart services:
echo   %COMPOSE_CMD% -f "%COMPOSE_FILE%" restart
echo.

:: Show container status
echo Current container status:
%COMPOSE_CMD% -f "%COMPOSE_FILE%" ps

pause
