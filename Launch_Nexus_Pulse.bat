@echo off
TITLE H.Huddair's Nexus-Pulse [Level 2 Enterprise]
cd /d "C:\Users\STONE\Desktop\rabbi"

echo ==============================================================================
echo                 H.HUDDAIR'S NEXUS-PULSE [LEVEL 2 ENTERPRISE]
echo             Autonomous B2B Lead Engine ^& Anti-Theft Fortress
echo ==============================================================================

:: 1. Check if port 8000 is already active
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [NOTICE] Port 8000 is already active! Nexus-Pulse server is running.
    echo [LAUNCHER] Opening GUI Dashboard in default browser: http://127.0.0.1:8000/
    echo ==============================================================================
    start "" "http://127.0.0.1:8000/"
    exit /b 0
)

:: 2. Port 8000 is free: Start Uvicorn server in the background
echo [1/2] Port 8000 is free. Starting Nexus-Pulse Uvicorn server in background...
start "Nexus-Pulse Server" /MIN python -m uvicorn api.app:app --host 127.0.0.1 --port 8000 --app-dir "C:\Users\STONE\Desktop\rabbi"

:: 3. Wait for Uvicorn to bind port 8000 (up to 10 attempts)
set ATTEMPTS=0
:wait_loop
set /a ATTEMPTS+=1
ping 127.0.0.1 -n 2 >nul 2>&1
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 goto launch_browser
if %ATTEMPTS% LSS 10 goto wait_loop

:launch_browser
echo [2/2] Server is ready! Launching GUI Dashboard: http://127.0.0.1:8000/
echo ==============================================================================
start "" "http://127.0.0.1:8000/"
