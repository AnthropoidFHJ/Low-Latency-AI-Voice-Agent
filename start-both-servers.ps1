Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " Real-Time AI Voice Agent - Dual Server Startup" -ForegroundColor Cyan  
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

if (!(Test-Path "backend") -or !(Test-Path "frontend")) {
    Write-Host "ERROR: Please run this script from the project root directory" -ForegroundColor Red
    Write-Host "Current directory should contain both 'backend' and 'frontend' folders" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

$env:GOOGLE_API_KEY = $env:GOOGLE_API_KEY
$env:ENABLE_AUTH = "false"
$env:DEBUG = "true"
$env:LOG_LEVEL = "INFO"

Write-Host "Starting Backend Server (FastAPI)..." -ForegroundColor Yellow
Write-Host "- Host: localhost:8000" -ForegroundColor Gray
Write-Host "- Authentication: Disabled" -ForegroundColor Gray
Write-Host "- Debug Mode: Enabled" -ForegroundColor Gray
Write-Host ""

$backendProcess = Start-Process -FilePath "cmd" -ArgumentList "/k", "cd /d $PWD\backend && D:\jibon\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -WindowStyle Normal -PassThru

Write-Host "Waiting 3 seconds for backend to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 3

Write-Host "Starting Frontend Server (Next.js)..." -ForegroundColor Yellow  
Write-Host "- URL: http://localhost:3000" -ForegroundColor Gray
Write-Host "- Hot Reload: Enabled" -ForegroundColor Gray
Write-Host ""

$frontendProcess = Start-Process -FilePath "cmd" -ArgumentList "/k", "cd /d $PWD\frontend && npm run dev" -WindowStyle Normal -PassThru

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host " Both servers are now running:" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host " Backend:  http://localhost:8000 (API endpoints)" -ForegroundColor White
Write-Host " Frontend: http://localhost:3000 (Voice Interface)" -ForegroundColor White
Write-Host ""
Write-Host " No authentication required - just open the frontend URL!" -ForegroundColor Cyan
Write-Host ""
Write-Host " To stop servers: Close the command windows or press Ctrl+C" -ForegroundColor Gray
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Press any key to exit this launcher..." -ForegroundColor Yellow
Read-Host
