# SLB Coliving PG — Backend Runner Script
# Sets the virtual environment path and starts the FastAPI server

$ErrorActionPreference = "Stop"

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  Starting SLB Coliving PG FastAPI Backend...    " -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

$VenvPython = ".\backend\venv\Scripts\python.exe"
$VenvScripts = ".\backend\venv\Scripts"

if (-not (Test-Path $VenvPython)) {
    Write-Host "[!] Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv backend/venv
    & ".\backend\venv\Scripts\pip.exe" install -r .\backend\requirements.txt
}

# Add venv to PATH so Prisma CLI binaries can find prisma-client-py on Windows
$env:PATH = "$((Resolve-Path $VenvScripts).Path);$env:PATH"

Write-Host "[+] Local Server: http://localhost:8000" -ForegroundColor Green
Write-Host "[+] Admin Portal: http://localhost:8000/admin" -ForegroundColor Green
Write-Host "[+] API Docs:     http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Default Admin Login:" -ForegroundColor Yellow
Write-Host "  Email:    admin@slbcoliving.com" -ForegroundColor White
Write-Host "  Password: admin123" -ForegroundColor White
Write-Host "-------------------------------------------------"

& $VenvPython -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
