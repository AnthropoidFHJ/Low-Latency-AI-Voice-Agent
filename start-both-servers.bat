@echo off
REM Real-Time AI Voice Agent - Start Both Servers
REM This script starts both backend and frontend servers simultaneously

echo ================================================================
echo  Real-Time AI Voice Agent - Dual Server Startup
echo ================================================================
echo.
echo Starting both backend (Python/FastAPI) and frontend (Next.js)...
echo.

REM Check if we're in the right directory
if not exist "backend" (
    echo ERROR: Please run this script from the project root directory
    echo Current directory should contain both 'backend' and 'frontend' folders
    pause
    exit /b 1
)

if not exist "frontend" (
    echo ERROR: Frontend directory not found
    echo Please ensure you're in the project root directory
    pause
    exit /b 1
)

REM Set environment variables for backend
set GOOGLE_API_KEY=%GOOGLE_API_KEY%
set ENABLE_AUTH=false
set DEBUG=true
set LOG_LEVEL=INFO
set HOST=0.0.0.0
set PORT=8000

echo Starting Backend Server (FastAPI)...
echo - Host: %HOST%:%PORT%
echo - Authentication: Disabled
echo - Debug Mode: Enabled
echo.

REM Start backend in a new command window
start "Voice Agent Backend" cmd /k "cd /d %~dp0backend && echo Backend Server Starting... && D:\jibon\.venv\Scripts\python.exe -m uvicorn app.main:app --host %HOST% --port %PORT% --reload && echo Backend server stopped. && pause"

REM Wait a moment for backend to initialize
echo Waiting 3 seconds for backend to initialize...
timeout /t 3 /nobreak >nul

echo Starting Frontend Server (Next.js)...
echo - URL: http://localhost:3000
echo - Hot Reload: Enabled
echo.

REM Start frontend in a new command window
start "Voice Agent Frontend" cmd /k "cd /d %~dp0frontend && echo Frontend Server Starting... && npm run dev && echo Frontend server stopped. && pause"

echo.
echo ================================================================
echo  Both servers are starting in separate windows:
echo ================================================================
echo  Backend:  http://localhost:8000 (API endpoints)
echo  Frontend: http://localhost:3000 (Voice Interface)
echo.
echo  No authentication required - just open the frontend URL!
echo.
echo  To stop servers: Close the respective command windows
echo  or press Ctrl+C in each window
echo ================================================================
echo.

REM Wait for user input before closing this window
echo Press any key to exit this launcher window...
pause >nul
