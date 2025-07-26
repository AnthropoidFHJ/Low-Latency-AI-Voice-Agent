#!/bin/bash

echo "Starting Real-Time Voice Agent Backend (No Auth)"
echo "========================================"

# Set environment variables
export GOOGLE_API_KEY="${GOOGLE_API_KEY:-your_api_key_here}"
export ENABLE_AUTH=false
export DEBUG=true
export LOG_LEVEL=INFO
export HOST=0.0.0.0
export PORT=8000


cd backend
python -m uvicorn app.main:app --host $HOST --port $PORT --reload

echo "Backend server started at http://localhost:8000"
echo "No authentication required - ready to accept connections!"
