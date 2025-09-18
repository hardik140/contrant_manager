@echo off
echo Starting Enhanced Contract Manager API...
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Check if we're in the right directory
if not exist "main.py" (
    echo Error: main.py not found. Please run this script from the backend directory.
    pause
    exit /b 1
)

:: Install dependencies if requirements.txt exists
if exist "requirements.txt" (
    echo Installing/updating dependencies...
    pip install -r requirements.txt
    echo.
)

:: Start the server
echo Starting server on http://127.0.0.1:8000
echo Press Ctrl+C to stop the server gracefully
echo.

python main.py

echo.
echo Server stopped.
pause
