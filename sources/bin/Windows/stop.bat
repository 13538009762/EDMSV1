@echo off
setlocal

:: EDMS Docker Stop Script for Windows

set SCRIPT_DIR=%~dp0
set DOCKER_DIR=%SCRIPT_DIR%..\..\docker\
set COMPOSE_FILE=%SCRIPT_DIR%..\docker-compose.yml

echo ============================================
echo    EDMS Docker Stop Script
echo ============================================
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

:: Stop and remove containers
echo Stopping EDMS services...
%COMPOSE_CMD% -f "%COMPOSE_FILE%" down
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to stop services
    pause
    exit /b 1
)

echo.
echo [OK] Services stopped successfully
pause
