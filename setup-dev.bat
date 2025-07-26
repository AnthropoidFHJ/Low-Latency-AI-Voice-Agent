@echo off
REM Real-Time AI Voice Agent - Development Setup Script (Windows)
REM This script sets up the complete development environment on Windows

echo 🎤 Setting up Real-Time AI Voice Agent Development Environment
echo ==============================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.8+ is required but not installed
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js 18+ is required but not installed
    exit /b 1
)

echo [INFO] System requirements check completed

REM Setup backend
echo [SETUP] Setting up backend environment...
cd backend

REM Create virtual environment
if not exist "venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install dependencies
echo [INFO] Installing Python dependencies...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo [INFO] Creating backend .env file...
    copy .env.example .env
    echo [WARNING] Please update .env file with your API keys!
)

cd ..
echo [INFO] Backend setup completed

REM Setup frontend
echo [SETUP] Setting up frontend environment...
cd frontend

REM Install dependencies
echo [INFO] Installing Node.js dependencies...
npm install

REM Create .env.local file if it doesn't exist
if not exist ".env.local" (
    echo [INFO] Creating frontend .env.local file...
    copy .env.example .env.local
)

cd ..
echo [INFO] Frontend setup completed

REM Create development scripts
echo [SETUP] Creating development scripts...

REM Backend development script
echo @echo off > dev-backend.bat
echo echo 🚀 Starting backend development server... >> dev-backend.bat
echo cd backend >> dev-backend.bat
echo call venv\Scripts\activate.bat >> dev-backend.bat
echo python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 >> dev-backend.bat

REM Frontend development script
echo @echo off > dev-frontend.bat
echo echo 🎨 Starting frontend development server... >> dev-frontend.bat
echo cd frontend >> dev-frontend.bat
echo npm run dev >> dev-frontend.bat

echo [INFO] Development scripts created

echo.
echo 🎉 Setup completed successfully!
echo.
echo Next steps:
echo 1. Update backend\.env with your Google API key
echo 2. Update frontend\.env.local if needed
echo 3. Run 'dev-backend.bat' and 'dev-frontend.bat' in separate terminals
echo.
echo Development URLs:
echo - Backend API: http://localhost:8000
echo - Frontend: http://localhost:3000
echo - API Docs: http://localhost:8000/docs
echo.
echo Performance targets:
echo - Voice-to-Voice Latency: ^<500ms  
echo - Connection Setup: ^<2 seconds
echo - Form Operations: ^<1 second

pause
