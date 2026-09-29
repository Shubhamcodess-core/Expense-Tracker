@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo        Personal Expense Tracker - Server Starter        
echo ========================================================
echo.

:: Check if Node.js is installed
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js is not found in your system PATH.
    echo Please install Node.js from https://nodejs.org/ to run the server.
    echo.
    pause
    exit /b 1
)

:: Check if server is already running on port 3000
netstat -ano | findstr :3000 | findstr LISTENING >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [INFO] Server is already running on http://localhost:3000
    echo Opening browser...
    start http://localhost:3000
    ping -n 3 127.0.0.1 >nul
    exit /b 0
)

echo [1/2] Starting Node.js backend server...
start "Personal Expense Tracker Server" cmd /k "node server\server.js"

:: Wait for server to initialize
echo [2/2] Waiting for server to initialize...
ping -n 3 127.0.0.1 >nul

:: Open browser
echo Opening http://localhost:3000 in your default browser...
start http://localhost:3000

echo.
echo Server is running successfully!
echo - Web App URL : http://localhost:3000
echo - Data Storage: Google Drive (users.csv & per-user CSVs)
echo.
echo You can close this window. To stop the server, run stop.bat
ping -n 3 127.0.0.1 >nul
exit /b 0
