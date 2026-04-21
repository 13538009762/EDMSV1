@echo off
REM Stop EDMS services in manual deployment mode
echo Stopping EDMS services...

REM Kill Python processes (backend)
taskkill /F /IM python.exe >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Backend service stopped.
) else (
    echo No backend process found or already stopped.
)

REM Kill Node.js processes (frontend)
taskkill /F /IM node.exe >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Frontend service stopped.
) else (
    echo No frontend process found or already stopped.
)

echo All services stopped successfully!
pause