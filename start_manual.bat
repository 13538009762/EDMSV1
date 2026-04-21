@echo off
REM Start EDMS services in manual deployment mode
echo Starting EDMS services (manual deployment)...

REM Start backend in new window
start "EDMS Backend" cmd /k "%~dp0\backend_start.bat"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in new window  
start "EDMS Frontend" cmd /k "%~dp0\frontend_start.bat"

echo Both services are starting in separate windows...
echo Frontend will be available at: http://localhost:5173
echo Backend API is running at: http://127.0.0.1:5000
pause