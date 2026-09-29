@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo        Personal Expense Tracker - Server Stopper        
echo ========================================================
echo.

echo Looking for running server on port 3000...
set "STOPPED=0"

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    echo Stopping server process PID: %%a...
    taskkill /F /T /PID %%a >nul 2>&1
    set "STOPPED=1"
)

:: Also close any window titled "Personal Expense Tracker Server"
taskkill /FI "WINDOWTITLE eq Personal Expense Tracker Server*" /F >nul 2>&1

if "%STOPPED%"=="1" (
    echo.
    echo Server has been stopped successfully.
) else (
    echo.
    echo No server was found running on port 3000.
)

echo.
pause
