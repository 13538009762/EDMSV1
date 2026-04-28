@echo off
REM Start EDMS frontend service (manual deployment)
echo Starting EDMS frontend service...

REM Change to frontend directory
cd /d "%~dp0"
cd sources\frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing npm dependencies...
    
    REM Check if cnpm is available, otherwise use npm with legacy peer deps
    where cnpm >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo Using cnpm...
        cnpm install
    ) else (
        echo Using npm with --legacy-peer-deps...
        npm install --legacy-peer-deps
    )
    
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install dependencies!
        pause
        exit /b %ERRORLEVEL%
    )
)

REM Start Vue development server
echo Starting Vue frontend on http://localhost:5173

where cnpm >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Using cnpm run dev...
    cnpm run dev
) else (
    echo Using npm run dev...
    npm run dev
)

if %ERRORLEVEL% NEQ 0 (
    echo Frontend failed to start!
    pause
    exit /b %ERRORLEVEL%
)