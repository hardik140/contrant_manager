#!/bin/bash

# Contract Manager Backend Startup Script

echo "Starting Contract Manager Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" ]]; then
    # Windows Git Bash
    source venv/Scripts/activate
else
    # Linux/Mac
    source venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Please create one with your MongoDB URI and Gemini API key."
    echo "Example .env content:"
    echo "MONGO_URI=mongodb://localhost:27017/"
    echo "GEMINI_API_KEY=your_gemini_api_key_here"
fi

# Start the server
echo "Starting FastAPI server..."
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
