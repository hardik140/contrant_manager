@echo off
REM Contract Manager Backend Startup Script for Windows

echo Starting Contract Manager Backend...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Check if .env file exists
if not exist ".env" (
    echo Warning: .env file not found. Please create one with your MongoDB URI and Gemini API key.
    echo Example .env content:
    echo MONGO_URI=mongodb://localhost:27017/
    echo GEMINI_API_KEY=your_gemini_api_key_here
)

REM Start the server
echo Starting FastAPI server...
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
