@echo off
REM ===============================================================================
REM                    🚀 QUICK START - Voice Agent
REM ===============================================================================
REM Simple one-click launcher for the Real-Time AI Voice Agent
REM This script automatically starts both backend and frontend servers

title Voice Agent - Quick Start

cls
echo.
echo ===============================================================================
echo                    🎤 REAL-TIME AI VOICE AGENT - QUICK START 🎤
echo ===============================================================================
echo.

REM Basic validation
if not exist "backend\app\main.py" (
    echo ❌ ERROR: Please run this script from the project root directory
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo ❌ ERROR: Virtual environment not found. Please run setup-dev.bat first
    pause
    exit /b 1
)

echo 🔧 Starting Backend Server...
start "Voice Agent Backend" /D "%~dp0backend" "%~dp0.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

REM Wait for backend to initialize
timeout /t 2 /nobreak >nul

echo 🌐 Starting Frontend Server...
start "Voice Agent Frontend" /D "%~dp0frontend" cmd /k "npm run dev"

echo.
echo ===============================================================================
echo                              🎉 SERVERS STARTED! 🎉
echo ===============================================================================
echo.
echo 🔧 Backend:  http://localhost:8000
echo 🌐 Frontend: http://localhost:3000
echo.
echo The voice agent is now ready! Press any key to exit...
pause >nul
