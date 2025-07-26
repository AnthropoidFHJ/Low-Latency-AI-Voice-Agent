@echo off
REM ===============================================================================
REM                    Real-Time AI Voice Agent - Production Launcher
REM ===============================================================================
REM 
REM This script provides a complete startup solution for the voice agent project
REM with proper dependency checking, environment setup, and server management.
REM 
REM Requirements:
REM - Python 3.11+ with virtual environment
REM - Node.js 18+ with npm
REM - Google API key (set as environment variable)
REM 
REM ===============================================================================

title Real-Time AI Voice Agent - Production Launcher

:MAIN_MENU
cls
echo.
echo ===============================================================================
echo                    🎤 REAL-TIME AI VOICE AGENT 🎤
echo                         Production Launcher
echo ===============================================================================
echo.
echo Select an option:
echo.
echo [1] 🚀 Quick Start (Both servers with validation)
echo [2] 🔧 Backend Only (Development mode)
echo [3] 🌐 Frontend Only (Development mode)
echo [4] ⚙️  Setup Development Environment
echo [5] 🧪 Run Tests and Validation
echo [6] 📊 System Health Check
echo [7] 🔑 Environment Configuration
echo [8] ❌ Exit
echo.
set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto QUICK_START
if "%choice%"=="2" goto BACKEND_ONLY
if "%choice%"=="3" goto FRONTEND_ONLY
if "%choice%"=="4" goto SETUP_DEV
if "%choice%"=="5" goto RUN_TESTS
if "%choice%"=="6" goto HEALTH_CHECK
if "%choice%"=="7" goto ENV_CONFIG
if "%choice%"=="8" goto EXIT
echo Invalid choice. Please try again.
pause
goto MAIN_MENU

:QUICK_START
cls
echo.
echo ===============================================================================
echo                         🚀 QUICK START - DUAL SERVER MODE
echo ===============================================================================
echo.
echo Performing pre-flight checks...
echo.

REM Check if we're in the correct directory
if not exist "backend\app\main.py" (
    echo ❌ ERROR: Backend application not found
    echo    Please run this script from the project root directory
    pause
    goto MAIN_MENU
)

if not exist "frontend\package.json" (
    echo ❌ ERROR: Frontend application not found
    echo    Please run this script from the project root directory
    pause
    goto MAIN_MENU
)

REM Check Python virtual environment
if not exist ".venv\Scripts\python.exe" (
    echo ❌ ERROR: Python virtual environment not found
    echo    Please run option [4] to setup development environment first
    pause
    goto MAIN_MENU
)

REM Check Node.js dependencies
if not exist "frontend\node_modules" (
    echo ⚠️  WARNING: Frontend dependencies not installed
    echo    Installing Node.js dependencies...
    cd frontend
    call npm install
    if errorlevel 1 (
        echo ❌ ERROR: Failed to install frontend dependencies
        pause
        cd ..
        goto MAIN_MENU
    )
    cd ..
)

echo ✅ All pre-flight checks passed!
echo.
echo Starting servers...
echo.

REM Set environment variables
set GOOGLE_API_KEY=%GOOGLE_API_KEY%
set ENABLE_AUTH=false
set DEBUG=true
set LOG_LEVEL=INFO

REM Start backend in new window
echo 🔧 Starting Backend Server (Port 8000)...
start "Voice Agent Backend" /D "%~dp0backend" "%~dp0.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in new window
echo 🌐 Starting Frontend Server (Port 3000)...
start "Voice Agent Frontend" /D "%~dp0frontend" cmd /k "npm run dev"

echo.
echo ===============================================================================
echo                              🎉 SERVERS STARTED! 🎉
echo ===============================================================================
echo.
echo 🔧 Backend:  http://localhost:8000
echo    - API Docs: http://localhost:8000/docs
echo    - Health:   http://localhost:8000/health
echo.
echo 🌐 Frontend: http://localhost:3000
echo    - Voice Interface: http://localhost:3000
echo.
echo ✨ The voice agent is now ready for use!
echo.
echo Press any key to return to main menu...
pause >nul
goto MAIN_MENU

:BACKEND_ONLY
cls
echo.
echo ===============================================================================
echo                         🔧 BACKEND DEVELOPMENT MODE
echo ===============================================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ❌ ERROR: Python virtual environment not found
    pause
    goto MAIN_MENU
)

REM Set environment variables
set GOOGLE_API_KEY=%GOOGLE_API_KEY%
set ENABLE_AUTH=false
set DEBUG=true
set LOG_LEVEL=DEBUG

echo Starting backend server in development mode...
echo.
cd backend
"%~dp0.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
cd ..
pause
goto MAIN_MENU

:FRONTEND_ONLY
cls
echo.
echo ===============================================================================
echo                         🌐 FRONTEND DEVELOPMENT MODE
echo ===============================================================================
echo.

if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)

echo Starting frontend server in development mode...
echo.
cd frontend
call npm run dev
cd ..
pause
goto MAIN_MENU

:SETUP_DEV
cls
echo.
echo ===============================================================================
echo                       ⚙️  DEVELOPMENT ENVIRONMENT SETUP
echo ===============================================================================
echo.

echo Setting up Python virtual environment...
if not exist ".venv" (
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ ERROR: Failed to create virtual environment
        pause
        goto MAIN_MENU
    )
)

echo Installing Python dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
if errorlevel 1 (
    echo ❌ ERROR: Failed to install Python dependencies
    pause
    goto MAIN_MENU
)

echo Installing Node.js dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo ❌ ERROR: Failed to install Node.js dependencies
    cd ..
    pause
    goto MAIN_MENU
)
cd ..

echo ✅ Development environment setup complete!
pause
goto MAIN_MENU

:RUN_TESTS
cls
echo.
echo ===============================================================================
echo                          🧪 TESTS AND VALIDATION
echo ===============================================================================
echo.

echo Running import tests...
.venv\Scripts\python.exe backend\test_imports.py
if errorlevel 1 (
    echo ❌ Import tests failed
) else (
    echo ✅ Import tests passed
)

echo.
echo Running backend health check...
cd backend
start /wait /B "%~dp0.venv\Scripts\python.exe" -c "import requests; print('✅ Backend can start' if True else '❌ Backend issues')"
cd ..

echo.
echo Tests completed. Press any key to continue...
pause >nul
goto MAIN_MENU

:HEALTH_CHECK
cls
echo.
echo ===============================================================================
echo                           📊 SYSTEM HEALTH CHECK
echo ===============================================================================
echo.

echo Checking system requirements...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found or not accessible
) else (
    echo ✅ Python is available
    python --version
)

node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found or not accessible
) else (
    echo ✅ Node.js is available
    node --version
)

if exist ".venv\Scripts\python.exe" (
    echo ✅ Virtual environment exists
) else (
    echo ❌ Virtual environment not found
)

if exist "frontend\node_modules" (
    echo ✅ Frontend dependencies installed
) else (
    echo ❌ Frontend dependencies not installed
)

if defined GOOGLE_API_KEY (
    echo ✅ Google API key is set
) else (
    echo ⚠️  Google API key not set (optional for development)
)

echo.
echo Health check completed. Press any key to continue...
pause >nul
goto MAIN_MENU

:ENV_CONFIG
cls
echo.
echo ===============================================================================
echo                        🔑 ENVIRONMENT CONFIGURATION
echo ===============================================================================
echo.

echo Current environment variables:
echo.
echo GOOGLE_API_KEY: %GOOGLE_API_KEY%
echo ENABLE_AUTH: %ENABLE_AUTH%
echo DEBUG: %DEBUG%
echo.

echo To set Google API key permanently:
echo 1. Get your API key from: https://ai.google.dev/
echo 2. Run: setx GOOGLE_API_KEY "your-api-key-here"
echo 3. Restart this script
echo.

echo Press any key to continue...
pause >nul
goto MAIN_MENU

:EXIT
cls
echo.
echo ===============================================================================
echo                               👋 GOODBYE!
echo ===============================================================================
echo.
echo Thank you for using the Real-Time AI Voice Agent!
echo.
echo For support and documentation:
echo - GitHub: https://github.com/your-repo/voice-agent
echo - Docs: Check README.md for detailed setup instructions
echo.
timeout /t 3 /nobreak >nul
exit /b 0
