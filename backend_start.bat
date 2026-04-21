@echo off
REM Start EDMS backend service (manual deployment)
echo Starting EDMS backend service...

REM Change to backend directory
cd /d "%~dp0"
cd sources\backend

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating Python virtual environment...
    python -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to create virtual environment!
        pause
        exit /b %ERRORLEVEL%
    )
)

REM Activate virtual environment and install dependencies
echo Activating virtual environment and installing dependencies...
call .venv\Scripts\activate.bat
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies!
    pause
    exit /b %ERRORLEVEL%
)

REM Start Flask backend
echo Starting Flask backend on http://127.0.0.1:5000
python wsgi.py

if %ERRORLEVEL% NEQ 0 (
    echo Backend failed to start!
    pause
    exit /b %ERRORLEVEL%
)