# Enhanced Contract Manager API Startup Script
Write-Host "Starting Enhanced Contract Manager API..." -ForegroundColor Green
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python version: $pythonVersion" -ForegroundColor Blue
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "main.py")) {
    Write-Host "Error: main.py not found. Please run this script from the backend directory." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install dependencies if requirements.txt exists
if (Test-Path "requirements.txt") {
    Write-Host "Installing/updating dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    Write-Host ""
}

# Start the server with better error handling
Write-Host "Starting server on http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server gracefully" -ForegroundColor Yellow
Write-Host ""

try {
    python main.py
} catch {
    Write-Host "Server encountered an error: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "Server stopped." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
}
