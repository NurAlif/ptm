@echo off
:: Set window title and color for the controller
title LingoJourn Manager (Controller)
color 0B

echo ===================================================
echo       LingoJourn Monitoring System Launcher
echo ===================================================
echo(
echo [1/2] Launching Backend (Uvicorn on port 5290)...
start "LingoJourn Backend" cmd /k "cd /d "%~dp0admin_back" && .venv\Scripts\activate && uvicorn app.main:app --host 127.0.0.1 --port 5290 --reload"

echo [2/2] Launching Frontend (Vite on port 5291)...
start "LingoJourn Frontend" cmd /k "cd /d "%~dp0admin_front" && npx vite"
echo(
echo ===================================================
echo   Status: Both servers started in separate windows!
echo(
echo   - You can see logs/output in the respective windows.
echo   - To stop both servers instantly, press any key here.
echo ===================================================
echo(
pause

echo(
echo Stopping all launched servers...
:: Terminate standard processes by window title matches
taskkill /FI "WINDOWTITLE eq LingoJourn Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq LingoJourn Frontend*" /T /F >nul 2>&1

echo(
echo ===================================================
echo   ✔ Both servers stopped successfully!
echo   Goodbye!
echo ===================================================
%SystemRoot%\System32\timeout.exe /t 3 >nul
