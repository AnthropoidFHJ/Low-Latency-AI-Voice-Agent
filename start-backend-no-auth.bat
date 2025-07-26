@echo off
REM Simple startup script for Windows without authentication

echo Starting Real-Time Voice Agent Backend (No Auth)
echo ========================================

REM Set environment variables
set GOOGLE_API_KEY=%GOOGLE_API_KEY%
set ENABLE_AUTH=false
set DEBUG=true
set LOG_LEVEL=INFO
set HOST=0.0.0.0
set PORT=8000

REM Navigate to backend directory
cd backend

echo Starting server without authentication...
D:\jibon\.venv\Scripts\python.exe -m uvicorn app.main:app --host %HOST% --port %PORT% --reload

echo Backend server started at http://localhost:8000
echo No authentication required - ready to accept connections!
